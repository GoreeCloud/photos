package com.goreecloud.photos

import android.content.ContentResolver
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.provider.OpenableColumns
import java.io.ByteArrayOutputStream
import java.io.File
import java.security.MessageDigest
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.util.UUID

data class Photo(
    val id: String, val name: String, val mediaType: String,
    val favorite: Boolean, val bytes: Long, val sha256: String
)

enum class LibraryView { ALL, FAVORITES, TRASH }
data class PhotosPage(val items: List<Photo>, val total: Int)

/** Single-library API. Authentication lives only in process memory. */
class PhotosApi(private val context: Context) {
    companion object {
        const val PAGE_SIZE = 40
        private const val MAX_ORIGINAL = 512L * 1024 * 1024
        private const val MAX_THUMBNAIL = 6L * 1024 * 1024
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
                    obj.getString("media_type"), obj.getBoolean("favorite"),
                    obj.getLong("bytes"), obj.getString("sha256"))
            }
            return PhotosPage(items, body.getInt("total"))
        } finally { conn.disconnect() }
    }

    /**
     * Foreground-only export of one authenticated original.
     *
     * First downloads and verifies the complete original in app-private cache.
     * Only afterwards opens the explicit system document-picker destination.
     * A failed provider write may leave a partial user-chosen document; it is
     * never silently deleted, so the user can inspect/recover their destination.
     */
    fun exportOriginal(photo: Photo, destination: Uri): Long {
        val originalToken = token ?: error("Unlock the library before exporting")
        require(UUID.fromString(photo.id).toString() == photo.id) { "Invalid photo ID" }
        require(photo.bytes in 1..MAX_ORIGINAL) { "Original exceeds the export limit" }
        require(Regex("^[0-9a-f]{64}$").matches(photo.sha256)) {
            "Invalid media checksum"
        }
        val conn = connection("/v1/assets/${photo.id}/original", "GET")
        val temp = try {
            File.createTempFile("photos-private-export-", ".part", context.cacheDir)
        } catch (failure: Exception) {
            conn.disconnect()
            throw failure
        }
        conn.readTimeout = 120000
        conn.setRequestProperty("Accept", "application/octet-stream")
        try {
            val status = conn.responseCode
            if (status != 200) error("Original is unavailable (HTTP $status)")
            val length = conn.contentLengthLong
            if (length > MAX_ORIGINAL || length > photo.bytes) error("Unexpected original size")
            val digest = MessageDigest.getInstance("SHA-256")
            var downloaded = 0L
            conn.inputStream.use { source ->
                temp.outputStream().use { sink ->
                    val buffer = ByteArray(65536)
                    while (true) {
                        val count = source.read(buffer)
                        if (count < 0) break
                        downloaded += count
                        if (downloaded > MAX_ORIGINAL || downloaded > photo.bytes) {
                            error("Original exceeds expected size")
                        }
                        digest.update(buffer, 0, count)
                        sink.write(buffer, 0, count)
                    }
                }
            }
            if (length >= 0 && downloaded != length) error("Incomplete original download")
            if (downloaded != photo.bytes) error("Original size verification failed")
            val checksum = digest.digest().joinToString("") {
                "%02x".format(it.toInt() and 0xff)
            }
            if (checksum != photo.sha256) error("Original checksum verification failed")
            if (token != originalToken) error("Library was locked while exporting")
            val resolver = context.contentResolver
            val output = resolver.openOutputStream(destination, "w")
                ?: error("Cannot write the selected destination")
            output.use { sink ->
                temp.inputStream().use { it.copyTo(sink, 65536) }
                sink.flush()
            }
            return downloaded
        } finally {
            conn.disconnect()
            temp.delete()
        }
    }

    fun thumbnail(id: String): Bitmap? {
        val conn = connection("/v1/assets/$id/thumbnail", "GET")
        try {
            val status = conn.responseCode
            if (status != 200) return null
            if (conn.contentLengthLong > MAX_THUMBNAIL) return null
            val data = ByteArrayOutputStream()
            conn.inputStream.use { stream ->
                val buffer = ByteArray(65536)
                var countTotal = 0L
                while (true) {
                    val count = stream.read(buffer)
                    if (count == -1) break
                    countTotal += count
                    if (countTotal > MAX_THUMBNAIL) return null
                    data.write(buffer, 0, count)
                }
            }
            val bytes = data.toByteArray()
            val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size, bounds)
            if (bounds.outWidth !in 1..2048 || bounds.outHeight !in 1..2048) return null
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
                    var uploaded = 0L
                    while (true) {
                        val count = source.read(buffer)
                        if (count == -1) break
                        uploaded += count
                        check(uploaded <= MAX_ORIGINAL) {
                            "Selected media exceeds the 512 MiB upload limit"
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
