package com.goreecloud.photos

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
        val api = PhotosApi(this)
        setContent {
            val scope = rememberCoroutineScope()
            var server by remember { mutableStateOf(api.server) }
            var password by remember { mutableStateOf("") }
            var unlocked by remember { mutableStateOf(false) }
            var loading by remember { mutableStateOf(false) }
            var notice by remember { mutableStateOf("") }
            var favorites by remember { mutableStateOf(false) }
            var photos by remember { mutableStateOf<List<Photo>>(emptyList()) }

            fun refresh() {
                scope.launch {
                    try { photos = withContext(Dispatchers.IO) { api.photos(favorites) } }
                    catch (e: Exception) { notice = e.message ?: "Unable to load library" }
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
                        refresh()
                    } catch (e: Exception) { notice = e.message ?: "Upload failed" }
                    finally { loading = false }
                }
            }

            // Foreground-only folder import. Access is granted by the system picker for this action.
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
                        refresh()
                    } catch (e: Exception) {
                        notice = e.message ?: "Folder import failed"
                    } finally {
                        loading = false
                    }
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
                                TextButton(onClick = { favorites = !favorites; refresh() }) {
                                    Text(if (favorites) "All" else "Favorites")
                                }
                                TextButton(enabled = !loading, onClick = {
                                    scope.launch {
                                        withContext(Dispatchers.IO) { runCatching { api.logout() } }
                                        unlocked = false; photos = emptyList()
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
                                loading = true; notice = ""
                                scope.launch {
                                    try {
                                        withContext(Dispatchers.IO) {
                                            api.configure(server)
                                            api.login(password)
                                        }
                                        password = ""
                                        unlocked = true
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
                                Text(if (favorites) "Favorites" else "Your collection",
                                    style = MaterialTheme.typography.titleLarge)
                                Column(horizontalAlignment = Alignment.End) {
                                    Button(enabled = !loading, onClick = {
                                        picker.launch(arrayOf("image/*", "video/mp4"))
                                    }) { Text("＋ Upload") }
                                    OutlinedButton(enabled = !loading, onClick = {
                                        folderPicker.launch(null)
                                    }) { Text("Import folder") }
                                }
                            }
                            Spacer(Modifier.height(16.dp))
                            if (photos.isEmpty()) Text("No photos in this view yet.")
                            LazyVerticalGrid(GridCells.Adaptive(minSize = 156.dp),
                                horizontalArrangement = Arrangement.spacedBy(10.dp),
                                verticalArrangement = Arrangement.spacedBy(12.dp)) {
                                items(photos, key = { it.id }) { photo ->
                                    Card(shape = RoundedCornerShape(18.dp)) {
                                        Column {
                                            var thumb by remember(photo.id) { mutableStateOf<android.graphics.Bitmap?>(null) }
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
                                            ) { Text(if (photo.mediaType.startsWith("video")) "Video" else "Photo") }
                                            Text(photo.name, maxLines = 1, overflow = TextOverflow.Ellipsis,
                                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp))
                                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                                TextButton(onClick = {
                                                    scope.launch {
                                                        try {
                                                            withContext(Dispatchers.IO) { api.favorite(photo.id, !photo.favorite) }
                                                            refresh()
                                                        } catch (e: Exception) { notice = e.message ?: "Error" }
                                                    }
                                                }) { Text(if (photo.favorite) "♥" else "♡") }
                                                TextButton(onClick = {
                                                    scope.launch {
                                                        try {
                                                            withContext(Dispatchers.IO) { api.trash(photo.id) }
                                                            refresh()
                                                        } catch (e: Exception) { notice = e.message ?: "Error" }
                                                    }
                                                }) { Text("Trash") }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        if (notice.isNotBlank()) {
                            Spacer(Modifier.height(12.dp))
                            Text(notice, color = MaterialTheme.colorScheme.primary, style = MaterialTheme.typography.bodySmall)
                        }
                        if (loading) LinearProgressIndicator(Modifier.fillMaxWidth())
                    }
                }
            }
        }
    }
}
