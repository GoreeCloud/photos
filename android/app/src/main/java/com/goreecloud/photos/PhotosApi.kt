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
import java.util.UUID

data class Photo(
    val id: String, val name: String, val mediaType: String,
    val favorite: Boolean, val bytes: Long
)

/** Single-library API. Authentication lives only in process memory. */
class PhotosApi(private val context: Context) {
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

    fun photos(favorites: Boolean = false): List<Photo> {
        val conn = connection("/v1/assets?limit=100" + if (favorites) "&favorite=true" else "", "GET")
        try {
            val array = JSONObject(read(conn)).getJSONArray("items")
            return (0 until array.length()).map { i ->
                val obj = array.getJSONObject(i)
                Photo(obj.getString("id"), obj.getString("filename"),
                    obj.getString("media_type"), obj.getBoolean("favorite"), obj.getLong("bytes"))
            }
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
                input.use { it.copyTo(out, 65536) }
                out.write("\r\n--$boundary--\r\n".toByteArray())
            }
            read(conn)
        } finally { conn.disconnect() }
    }
}
