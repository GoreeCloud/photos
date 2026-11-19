package com.goreecloud.photos

import android.graphics.Bitmap
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val api = PhotosApi(applicationContext)
        setContent {
            val scope = rememberCoroutineScope()
            var server by remember { mutableStateOf(api.server) }
            var password by remember { mutableStateOf("") }
            var unlocked by remember { mutableStateOf(false) }
            var loading by remember { mutableStateOf(false) }
            var notice by remember { mutableStateOf("") }
            var view by remember { mutableStateOf(LibraryView.ALL) }
            var query by remember { mutableStateOf("") }
            var activeSearch by remember { mutableStateOf("") }
            var pageIndex by remember { mutableIntStateOf(0) }
            var total by remember { mutableIntStateOf(0) }
            var requestId by remember { mutableIntStateOf(0) }
            var photos by remember { mutableStateOf<List<Photo>>(emptyList()) }

            fun refresh() {
                val id = ++requestId
                val requestedPage = pageIndex
                val requestedView = view
                val requestedSearch = activeSearch
                scope.launch {
                    try {
                        val result = withContext(Dispatchers.IO) {
                            api.photosPage(requestedView, requestedSearch, requestedPage)
                        }
                        if (id != requestId || !unlocked) return@launch
                        if (requestedPage > 0 && requestedPage * PhotosApi.PAGE_SIZE >= result.total) {
                            pageIndex = if (result.total == 0) 0 else (result.total - 1) / PhotosApi.PAGE_SIZE
                            refresh()
                            return@launch
                        }
                        photos = result.items
                        total = result.total
                    } catch (e: Exception) {
                        if (id == requestId && unlocked) notice = e.message ?: "Library request failed"
                    }
                }
            }

            fun chooseView(next: LibraryView) {
                view = next
                pageIndex = 0
                photos = emptyList()
                refresh()
            }

            fun actOn(photo: Photo, operation: String) {
                loading = true
                scope.launch {
                    try {
                        withContext(Dispatchers.IO) {
                            when (operation) {
                                "restore" -> api.restore(photo.id)
                                "trash" -> api.trash(photo.id)
                                "favorite" -> api.favorite(photo.id, !photo.favorite)
                            }
                        }
                        refresh()
                    } catch (e: Exception) { notice = e.message ?: "Photo action failed" }
                    finally { loading = false }
                }
            }

            val picker = rememberLauncherForActivityResult(
                ActivityResultContracts.OpenMultipleDocuments()
            ) { selected ->
                if (selected.isEmpty()) return@rememberLauncherForActivityResult
                loading = true
                scope.launch {
                    try {
                        withContext(Dispatchers.IO) { selected.forEach { api.upload(it) } }
                        notice = "${selected.size} photos or videos uploaded."
                        view = LibraryView.ALL
                        pageIndex = 0
                        refresh()
                    } catch (e: Exception) { notice = e.message ?: "Upload failed" }
                    finally { loading = false }
                }
            }

            // This picker is user-initiated, foreground-only, and does not persist a tree grant.
            val folderPicker = rememberLauncherForActivityResult(
                ActivityResultContracts.OpenDocumentTree()
            ) { tree ->
                if (tree == null) return@rememberLauncherForActivityResult
                loading = true
                notice = "Checking the selected folder..."
                scope.launch {
                    try {
                        val report = withContext(Dispatchers.IO) {
                            FolderImport(contentResolver, api).importFolder(tree) { scanned, count ->
                                if (scanned == count || scanned % 10 == 0) {
                                    runOnUiThread { notice = "Checking $scanned of $count selected files" }
                                }
                            }
                        }
                        notice = "${report.uploaded} uploaded · ${report.skipped} already stored · " +
                            "${report.inTrash} in trash · ${report.failed} failed"
                        view = LibraryView.ALL
                        pageIndex = 0
                        refresh()
                    } catch (e: Exception) {
                        notice = e.message ?: "Folder import failed"
                    } finally { loading = false }
                }
            }

            MaterialTheme {
                Scaffold(topBar = {
                    Surface(shadowElevation = 2.dp) {
                        Row(Modifier.fillMaxWidth().padding(16.dp),
                            verticalAlignment = Alignment.CenterVertically) {
                            Text("✦ Photos", style = MaterialTheme.typography.titleLarge,
                                modifier = Modifier.weight(1f))
                            if (unlocked) {
                                TextButton(enabled = !loading, onClick = { refresh() }) {
                                    Text("Refresh")
                                }
                                TextButton(enabled = !loading, onClick = {
                                    loading = true
                                    requestId++
                                    unlocked = false
                                    photos = emptyList()
                                    total = 0
                                    pageIndex = 0
                                    scope.launch {
                                        withContext(Dispatchers.IO) { runCatching { api.logout() } }
                                        loading = false
                                    }
                                }) { Text("Lock") }
                            }
                        }
                    }
                }) { padding ->
                    Column(Modifier.fillMaxSize().padding(padding).padding(16.dp)) {
                        if (!unlocked) {
                            Spacer(Modifier.height(36.dp))
                            Text("Your memories, your cloud", style = MaterialTheme.typography.headlineMedium)
                            Spacer(Modifier.height(20.dp))
                            OutlinedTextField(value = server, onValueChange = { server = it },
                                label = { Text("Server URL (HTTPS required remotely)") },
                                modifier = Modifier.fillMaxWidth())
                            OutlinedTextField(value = password, onValueChange = { password = it },
                                label = { Text("Library password") }, singleLine = true,
                                visualTransformation = PasswordVisualTransformation(),
                                modifier = Modifier.fillMaxWidth())
                            Spacer(Modifier.height(16.dp))
                            Button(enabled = !loading && password.isNotEmpty(), onClick = {
                                loading = true
                                notice = ""
                                scope.launch {
                                    try {
                                        withContext(Dispatchers.IO) {
                                            api.configure(server)
                                            api.login(password)
                                        }
                                        password = ""
                                        unlocked = true
                                        view = LibraryView.ALL
                                        pageIndex = 0
                                        refresh()
                                    } catch (e: Exception) { notice = e.message ?: "Unable to sign in" }
                                    finally { loading = false }
                                }
                            }, modifier = Modifier.fillMaxWidth()) { Text("Unlock library") }
                            Text("Sessions are kept in memory. No automatic photo access or backup.",
                                style = MaterialTheme.typography.bodySmall)
                        } else {
                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically) {
                                Text("Your collection", style = MaterialTheme.typography.titleLarge)
                                Column(horizontalAlignment = Alignment.End) {
                                    Button(enabled = !loading, onClick = {
                                        picker.launch(arrayOf("image/*", "video/mp4"))
                                    }) { Text("＋ Upload") }
                                    OutlinedButton(enabled = !loading, onClick = {
                                        folderPicker.launch(null)
                                    }) { Text("Import folder") }
                                }
                            }
                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                                LibraryView.entries.forEach { candidate ->
                                    val title = when (candidate) {
                                        LibraryView.ALL -> "All"
                                        LibraryView.FAVORITES -> "Favorites"
                                        LibraryView.TRASH -> "Trash"
                                    }
                                    TextButton(
                                        enabled = !loading,
                                        onClick = { chooseView(candidate) },
                                        colors = ButtonDefaults.textButtonColors(
                                            contentColor = if (view == candidate)
                                                MaterialTheme.colorScheme.primary
                                            else MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                    ) { Text(title) }
                                }
                            }
                            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                                OutlinedTextField(
                                    value = query, onValueChange = { query = it.take(128) },
                                    label = { Text("Search filenames") },
                                    singleLine = true,
                                    modifier = Modifier.weight(1f)
                                )
                                TextButton(enabled = !loading, onClick = {
                                    activeSearch = query
                                    pageIndex = 0
                                    refresh()
                                }) { Text("Find") }
                            }
                            Spacer(Modifier.height(10.dp))
                            if (photos.isEmpty()) Text("No photos in this view yet.")
                            LazyVerticalGrid(
                                columns = GridCells.Adaptive(minSize = 156.dp),
                                modifier = Modifier.weight(1f).fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(10.dp),
                                verticalArrangement = Arrangement.spacedBy(12.dp)
                            ) {
                                items(photos, key = { it.id }) { photo ->
                                    Card(shape = RoundedCornerShape(18.dp)) {
                                        Column {
                                            var thumb by remember(photo.id) { mutableStateOf<Bitmap?>(null) }
                                            LaunchedEffect(photo.id) {
                                                thumb = withContext(Dispatchers.IO) {
                                                    runCatching { api.thumbnail(photo.id) }.getOrNull()
                                                }
                                            }
                                            if (thumb != null) Image(
                                                bitmap = thumb!!.asImageBitmap(),
                                                contentDescription = photo.name,
                                                contentScale = ContentScale.Crop,
                                                modifier = Modifier.fillMaxWidth().height(136.dp)
                                            ) else Box(
                                                Modifier.fillMaxWidth().height(136.dp)
                                                    .background(MaterialTheme.colorScheme.surfaceVariant),
                                                contentAlignment = Alignment.Center
                                            ) {
                                                Text(if (photo.mediaType.startsWith("video")) "Video" else "Photo")
                                            }
                                            Text(photo.name, maxLines = 1, overflow = TextOverflow.Ellipsis,
                                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp))
                                            if (view == LibraryView.TRASH) {
                                                TextButton(enabled = !loading,
                                                    onClick = { actOn(photo, "restore") }) {
                                                    Text("Restore")
                                                }
                                            } else {
                                                Row(Modifier.fillMaxWidth(),
                                                    horizontalArrangement = Arrangement.SpaceBetween) {
                                                    TextButton(enabled = !loading,
                                                        onClick = { actOn(photo, "favorite") }) {
                                                        Text(if (photo.favorite) "♥" else "♡")
                                                    }
                                                    TextButton(enabled = !loading,
                                                        onClick = { actOn(photo, "trash") }) {
                                                        Text("Trash")
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            val lastPage = if (total == 0) 0 else (total - 1) / PhotosApi.PAGE_SIZE
                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically) {
                                Text("$total items · ${pageIndex + 1}/${lastPage + 1}",
                                    style = MaterialTheme.typography.bodySmall)
                                Row {
                                    TextButton(enabled = !loading && pageIndex > 0,
                                        onClick = { pageIndex--; refresh() }) { Text("Previous") }
                                    TextButton(enabled = !loading && pageIndex < lastPage,
                                        onClick = { pageIndex++; refresh() }) { Text("Next") }
                                }
                            }
                        }
                        if (notice.isNotBlank()) {
                            Text(notice, color = MaterialTheme.colorScheme.primary,
                                style = MaterialTheme.typography.bodySmall)
                        }
                        if (loading) LinearProgressIndicator(Modifier.fillMaxWidth())
                    }
                }
            }
        }
    }
}
