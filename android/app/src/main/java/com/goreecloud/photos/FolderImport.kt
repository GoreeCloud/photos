package com.goreecloud.photos

import android.content.ContentResolver
import android.net.Uri
import android.provider.DocumentsContract
import java.security.MessageDigest

/**
 * Foreground-only, user-directed folder import.
 *
 * The system document-tree picker grants access to one folder. We never request broad
 * media permissions, persist a tree grant, schedule a worker or retain credentials.
 */
data class FolderImportReport(
    val found: Int,
    val uploaded: Int,
    val skipped: Int,
    val inTrash: Int,
    val failed: Int
)

class FolderImport(
    private val resolver: ContentResolver,
    private val api: PhotosApi
) {
    companion object {
        private const val MAX_FILES = 500
        private const val MAX_SIZE = 512L * 1024L * 1024L
        private val SUPPORTED_TYPES = setOf(
            "image/jpeg", "image/png", "image/gif", "image/webp", "video/mp4"
        )
    }

    private fun folderFiles(tree: Uri): List<Uri> {
        val parent = DocumentsContract.getTreeDocumentId(tree)
        val children = DocumentsContract.buildChildDocumentsUriUsingTree(tree, parent)
        val result = mutableListOf<Uri>()
        resolver.query(
            children,
            arrayOf(
                DocumentsContract.Document.COLUMN_DOCUMENT_ID,
                DocumentsContract.Document.COLUMN_MIME_TYPE
            ),
            null, null, null
        )?.use { cursor ->
            while (cursor.moveToNext()) {
                val mime = cursor.getString(1) ?: continue
                if (mime in SUPPORTED_TYPES) {
                    if (result.size >= MAX_FILES) {
                        throw IllegalArgumentException(
                            "This folder has more than $MAX_FILES supported files. Choose a smaller folder."
                        )
                    }
                    val id = cursor.getString(0) ?: continue
                    result += DocumentsContract.buildDocumentUriUsingTree(tree, id)
                }
            }
        } ?: error("Could not read the selected folder")
        return result
    }

    private fun sha256(uri: Uri): String {
        val hash = MessageDigest.getInstance("SHA-256")
        val buffer = ByteArray(65536)
        var size = 0L
        val stream = resolver.openInputStream(uri) ?: error("Unable to read selected document")
        stream.use { input ->
            while (true) {
                val count = input.read(buffer)
                if (count == -1) break
                size += count
                if (size > MAX_SIZE) error("Selected document exceeds server size limit")
                hash.update(buffer, 0, count)
            }
        }
        return hash.digest().joinToString("") { "%02x".format(it.toInt() and 0xff) }
    }

    /** Run from Dispatchers.IO. Callback exposes only counts, never names or hashes. */
    fun importFolder(tree: Uri, progress: (Int, Int) -> Unit = { _, _ -> }): FolderImportReport {
        val docs = folderFiles(tree)
        val pending = mutableListOf<Pair<Uri, String>>()
        var failed = 0
        for ((index, uri) in docs.withIndex()) {
            try {
                pending += uri to sha256(uri)
            } catch (_: Exception) {
                failed++
            }
            progress(index + 1, docs.size)
        }
        var uploaded = 0
        var skipped = 0
        var inTrash = 0
        // Server preflight accepts at most 100 hashes and requires the current login.
        for (chunk in pending.chunked(100)) {
            val existing = api.existingHashes(chunk.map { it.second })
            for ((uri, digest) in chunk) {
                if (digest in existing) {
                    if (existing[digest] == true) inTrash++ else skipped++
                    continue
                }
                try {
                    api.upload(uri)
                    uploaded++
                } catch (e: IllegalStateException) {
                    // A concurrent import may race the preflight; the server is authoritative.
                    if (e.message?.startsWith("Duplicate file") == true) skipped++ else failed++
                } catch (_: Exception) {
                    failed++
                }
            }
        }
        return FolderImportReport(docs.size, uploaded, skipped, inTrash, failed)
    }
}
