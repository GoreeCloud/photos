package com.goreecloud.photos

import android.content.ContentResolver
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.provider.OpenableColumns
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.util.UUID

data class Photo(
    val id: String, val name: String, val mediaType: String,
    val favorite: Boolean, val bytes: Long
)

enum class LibraryView { ALL, FAVORITES, TRASH }
data class PhotosPage(val items: List<Photo>, val total: Int)

/** Single-library API. Authentication lives only in process memory. */
class PhotosApi(private val context: Context) {
    companion object {
        const val PAGE_SIZE = 40
        private const val MAX_MEDIA_BYTES = 512L * 1024L * 1024L
    }
    var server: String = "http://127.0.0.1:8787"
        private set
    private var token: String? = null

    fun configure(value: String) {
        val u = URL(value.trim().trimEnd('/'))
        require(u.protocol == "https" || (u.protocol == "http" &&
            u.host in setOf("localhost", "127.0.0.1", "::1"))) {
            "Remote servers require HTTPS."
        }
        require(u.userInfo == null && u.query == null && u.ref == null && u.path in setOf("", "/"))
        server = value.trim().trimEnd('/')
        token = null
    }

    private fun connection(path: String, method: String): HttpURLConnection {
        val connection = (URL(server + path).openConnection() as HttpURLConnection)
        connection.requestMethod = method
        connection.connectTimeout = 12000
        connection.readTimeout = 60000
        connection.useCaches = false
        connection.instanceFollowRedirects = false
        connection.setRequestProperty("Accept", "application/json")
        token?.let { connection.setRequestProperty("Authorization", "Bearer $it") }
        return connection
    }

    private fun read(connection: HttpURLConnection): String {
        val status = connection.responseCode
        val stream = if (status in 200..299) connection.inputStream else connection.errorStream
        val body = stream?.bufferedReader()?.use { it.readText() } ?: ""
        if (status !in 200..299) {
            val detail = try { JSONObject(body).optString("detail") } catch (_: Exception) { "" }
            throw IllegalStateException(if (detail.isNotBlank()) detail else "Server error $status")
        }
        return body
    }

    fun login(password: String) {
        val conn = connection("/v1/session", "POST")
        try {
            conn.doOutput = true
            conn.setRequestProperty("Content-Type", "application/json")
            conn.outputStream.use { it.write(JSONObject().put("password", password).toString().toByteArray()) }
            token = JSONObject(read(conn)).getString("access_token")
        } finally { conn.disconnect() }
    }

    fun logout() {
        try {
            val conn = connection("/v1/session", "DELETE")
            try { read(conn) } finally { conn.disconnect() }
        } finally { token = null }
    }

    /** Server-paged library query, including trash. Does not scan device storage. */
    fun photosPage(
        view: LibraryView = LibraryView.ALL, search: String = "", page: Int = 0
    ): PhotosPage {
        require(page in 0..25000) { "Page is out of range" }
        require(search.length <= 128)
        val encoded = URLEncoder.encode(search, Charsets.UTF_8.name())
        val path = "/v1/assets?limit=$PAGE_SIZE&offset=${page * PAGE_SIZE}" +
            "&favorite=${view == LibraryView.FAVORITES}&trashed=${view == LibraryView.TRASH}" +
            "&search=$encoded"
        val conn = connection(path, "GET")
        try {
            val body = JSONObject(read(conn))
            val array = body.getJSONArray("items")
            val items = (0 until array.length()).map { i ->
                val obj = array.getJSONObject(i)
                Photo(obj.getString("id"), obj.getString("filename"),
                    obj.getString("media_type"), obj.getBoolean("favorite"), obj.getLong("bytes"))
            }
            return PhotosPage(items, body.getInt("total"))
        } finally { conn.disconnect() }
    }

    fun thumbnail(id: String): Bitmap? {
        val conn = connection("/v1/assets/$id/thumbnail", "GET")
        try {
            val status = conn.responseCode
            if (status != 200) return null
            val bytes = conn.inputStream.use { it.readBytes() }
            return BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
        } finally { conn.disconnect() }
    }

    fun favorite(id: String, value: Boolean) {
        val conn = connection("/v1/assets/$id/favorite", "POST")
        try {
            conn.doOutput = true
            conn.setRequestProperty("Content-Type", "application/json")
            conn.outputStream.use { it.write(JSONObject().put("favorite", value).toString().toByteArray()) }
            read(conn)
        } finally { conn.disconnect() }
    }

    fun trash(id: String) {
        val conn = connection("/v1/assets/$id", "DELETE")
        try { read(conn) } finally { conn.disconnect() }
    }

    /** Existing hashes map to whether they are currently in the trash. */
    fun existingHashes(hashes: List<String>): Map<String, Boolean> {
        require(hashes.isNotEmpty() && hashes.size <= 100)
        val conn = connection("/v1/assets/lookup", "POST")
        try {
            conn.doOutput = true
            conn.setRequestProperty("Content-Type", "application/json")
            val body = JSONObject().put("hashes", JSONArray(hashes)).toString().toByteArray()
            conn.outputStream.use { it.write(body) }
            val items = JSONObject(read(conn)).getJSONArray("existing")
            return buildMap {
                for (i in 0 until items.length()) {
                    val item = items.getJSONObject(i)
                    put(item.getString("sha256"), item.getBoolean("trashed"))
                }
            }
        } finally { conn.disconnect() }
    }

    fun restore(id: String) {
        val conn = connection("/v1/assets/$id/restore", "POST")
        try { read(conn) } finally { conn.disconnect() }
    }

    /**
     * Stream one private original to a document newly created by Android's
     * ACTION_CREATE_DOCUMENT picker. The caller must choose the destination.
     * No blanket device-storage access or background transfer is involved.
     */
    fun saveOriginal(id: String, document: Uri): Long {
        require(UUID.fromString(id).toString() == id) { "Invalid original identifier" }
        require(document.scheme == "content") { "Select a document provider destination" }
        val conn = connection("/v1/assets/$id/original", "GET")
        try {
            conn.setRequestProperty("Accept", "application/octet-stream")
            val status = conn.responseCode
            check(status == 200) { "Original unavailable (HTTP $status)" }
            val reported = conn.contentLengthLong
            check(reported in -1..MAX_MEDIA_BYTES) { "Original exceeds 512 MiB maximum" }
            val output = context.contentResolver.openOutputStream(document, "wt")
                ?: error("Cannot write selected document")
            var received = 0L
            output.use { sink ->
                conn.inputStream.use { stream ->
                    val buffer = ByteArray(65536)
                    while (true) {
                        val count = stream.read(buffer)
                        if (count == -1) break
                        received += count
                        check(received <= MAX_MEDIA_BYTES) { "Original exceeds 512 MiB maximum" }
                        sink.write(buffer, 0, count)
                    }
                }
                sink.flush()
            }
            check(reported < 0 || received == reported) { "Original transfer was incomplete" }
            return received
        } catch (error: Exception) {
            // ACTION_CREATE_DOCUMENT created the output for this explicit
            // user action. Do not leave a partial private original behind.
            runCatching { context.contentResolver.delete(document, null, null) }
            throw error
        } finally {
            conn.disconnect()
        }
    }

    fun upload(uri: Uri) {
        val resolver: ContentResolver = context.contentResolver
        var name = "photo"
        resolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { cursor ->
            if (cursor.moveToFirst()) name = cursor.getString(0) ?: name
        }
        name = name.substringAfterLast('/').substringAfterLast('\\')
            .replace("\r", "").replace("\n", "").replace("\"", "").take(160)
        val boundary = "Photos-" + UUID.randomUUID().toString()
        val conn = connection("/v1/assets", "POST")
        try {
            conn.doOutput = true
            conn.setChunkedStreamingMode(65536)
            conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=$boundary")
            conn.outputStream.use { out ->
                out.write(("--$boundary\r\nContent-Disposition: form-data; name=\"file\"; filename=\"$name\"\r\n" +
                    "Content-Type: application/octet-stream\r\n\r\n").toByteArray())
                val input = resolver.openInputStream(uri) ?: error("Cannot read selected document")
                input.use { source ->
                    val buffer = ByteArray(65536)
                    var countBytes = 0L
                    while (true) {
                        val count = source.read(buffer)
                        if (count == -1) break
                        countBytes += count
                        check(countBytes <= MAX_MEDIA_BYTES) {
                            "Selected media exceeds 512 MiB limit"
                        }
                        out.write(buffer, 0, count)
                    }
                }
                out.write("\r\n--$boundary--\r\n".toByteArray())
            }
            read(conn)
        } finally { conn.disconnect() }
    }
}
