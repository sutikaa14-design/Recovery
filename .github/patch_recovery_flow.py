from pathlib import Path

def replace_or_fail(text, old, new, label):
    if old not in text:
        raise SystemExit(f"{label} not found")
    return text.replace(old, new, 1)

# RecoveryViewModel
p = Path("app/src/main/java/com/recoverx/app/ui/viewmodel/RecoveryViewModel.kt")
s = p.read_text()
s = replace_or_fail(s,
"""    fun openPreview(file: RecoverableFile) {
        _uiState.update { it.copy(currentScreen = ScreenState.Preview(file)) }
    }
""",
"""    fun openPreview(file: RecoverableFile) {
        _uiState.update { it.copy(currentScreen = ScreenState.Preview(file)) }
    }

    fun viewResultsDuringScan() {
        if (_uiState.value.foundFiles.isNotEmpty()) {
            _uiState.update { it.copy(currentScreen = ScreenState.FoundFiles) }
        }
    }

    fun recoverSingle(file: RecoverableFile) {
        val updated = _uiState.value.foundFiles.map {
            it.copy(isSelected = it.id == file.id)
        }
        _uiState.update {
            it.copy(
                foundFiles = updated,
                selectedCount = 1,
                selectedTotalBytes = file.sizeBytes,
                isAllSelected = false,
                isTargetDestinationDialogVisible = true
            )
        }
    }
""", "openPreview")
s = replace_or_fail(s,
"""    fun executeRecovery(targetTreeUri: Uri? = null) {
        hideDestinationDialog()
""",
"""    fun executeRecovery(targetTreeUri: Uri? = null) {
        if (_uiState.value.scanProgress.isScanning) {
            scanJob?.cancel()
        }
        hideDestinationDialog()
""", "executeRecovery")
p.write_text(s)

# MainActivity
p = Path("app/src/main/java/com/recoverx/app/MainActivity.kt")
s = p.read_text()
s = replace_or_fail(s,
"""                            ScanningScreen(
                                state = state,
                                onCancelScan = { viewModel.cancelScan() }
                            )""",
"""                            ScanningScreen(
                                state = state,
                                onCancelScan = { viewModel.cancelScan() },
                                onViewResults = { viewModel.viewResultsDuringScan() }
                            )""", "ScanningScreen call")
s = s.replace("onRecoverSingle = { viewModel.showDestinationDialog() }", "onRecoverSingle = { viewModel.recoverSingle(screen.file) }")
s = s.replace(
"""                                onCancelScan = {}
                            )""",
"""                                onCancelScan = {},
                                onViewResults = {}
                            )"""
)
p.write_text(s)

# ScanningScreen
p = Path("app/src/main/java/com/recoverx/app/ui/screens/ScanningScreen.kt")
s = p.read_text()
s = replace_or_fail(s,
"""fun ScanningScreen(
    state: UiState,
    onCancelScan: () -> Unit
) {""",
"""fun ScanningScreen(
    state: UiState,
    onCancelScan: () -> Unit,
    onViewResults: () -> Unit
) {""", "ScanningScreen signature")
s = replace_or_fail(s,
"""        Spacer(modifier = Modifier.height(20.dp))

        // Category Matrix""",
"""        if (state.foundFiles.isNotEmpty()) {
            Card(
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = DarkSurface),
                border = androidx.compose.foundation.BorderStroke(1.dp, CyanPrimary.copy(alpha = 0.35f)),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth().padding(14.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = "${state.foundFiles.size} file sudah ditemukan",
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            fontSize = 14.sp
                        )
                        Text(
                            text = "Hasil dapat direview dan dipulihkan sekarang. Pemindaian masih berlangsung.",
                            color = TextSecondary,
                            fontSize = 11.sp
                        )
                    }
                    Spacer(modifier = Modifier.width(10.dp))
                    Button(
                        onClick = onViewResults,
                        colors = ButtonDefaults.buttonColors(
                            containerColor = CyanPrimary,
                            contentColor = DarkBackground
                        ),
                        shape = RoundedCornerShape(10.dp)
                    ) {
                        Icon(Icons.Default.Visibility, contentDescription = null, modifier = Modifier.size(18.dp))
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Lihat Hasil", fontWeight = FontWeight.Bold, fontSize = 11.sp)
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        // Category Matrix""", "ScanningScreen live-results card")
p.write_text(s)

# RecoveryManager: make default recovery folder creation explicit and fail clearly.
p = Path("app/src/main/java/com/recoverx/app/data/recovery/RecoveryManager.kt")
s = p.read_text()
s = replace_or_fail(s,
"""        if (targetTreeUri == null && !defaultOutputDir.exists()) {
            defaultOutputDir.mkdirs()
        }""",
"""        if (targetTreeUri == null) {
            if (!defaultOutputDir.exists() && !defaultOutputDir.mkdirs()) {
                throw IllegalStateException("Folder pemulihan tidak dapat dibuat: ${defaultOutputDir.absolutePath}")
            }
            if (!defaultOutputDir.isDirectory || !defaultOutputDir.canWrite()) {
                throw IllegalStateException("Folder pemulihan tidak dapat ditulis: ${defaultOutputDir.absolutePath}")
            }
        }""", "default recovery folder")
p.write_text(s)

print("Recovery live-results/recovery patch applied")

# Post-process FoundFilesScreen after the existing thumbnail patch.
p = Path("app/src/main/java/com/recoverx/app/ui/screens/FoundFilesScreen.kt")
s = p.read_text()

for imp in [
    "import android.graphics.Bitmap",
    "import android.media.MediaMetadataRetriever",
    "import android.net.Uri",
    "import coil.compose.AsyncImage",
    "import kotlinx.coroutines.Dispatchers",
    "import kotlinx.coroutines.withContext",
    "import androidx.compose.foundation.lazy.grid.GridCells",
    "import androidx.compose.foundation.lazy.grid.items",
    "import androidx.compose.foundation.lazy.grid.LazyVerticalGrid",
    "import androidx.compose.foundation.shape.CircleShape",
    "import androidx.compose.ui.graphics.asImageBitmap",
    "import androidx.compose.ui.layout.ContentScale",
    "import androidx.compose.runtime.*"
]:
    if imp not in s:
        first_import = s.find("import ")
        s = s[:first_import] + imp + "\n" + s[first_import:]

s = s.replace("val isVideo = file.category == ScanCategory.VIDEOS",
"""val isVideo = file.category == ScanCategory.VIDEOS
    val mediaModel: Any? = file.uri ?: file.originalPath.takeIf { it.isNotBlank() }?.let { java.io.File(it) }""", 1)
s = s.replace("isPhoto && file.uri != null -> AsyncImage(model = file.uri,",
                    "isPhoto && mediaModel != null -> AsyncImage(model = mediaModel,", 1)
s = s.replace("isVideo && file.uri != null -> {",
                    "isVideo && mediaModel != null -> {", 1)
s = s.replace("VideoThumbnail(file.uri, Modifier.fillMaxSize())",
                    "VideoThumbnail(mediaModel, Modifier.fillMaxSize())", 1)

old_v = re.search(r"@Composable\s+private fun VideoThumbnail\([\s\S]*?\n}\n\n", s)
if old_v:
    new_v = '''@Composable
private fun VideoThumbnail(model: Any, modifier: Modifier = Modifier) {
    val context = androidx.compose.ui.platform.LocalContext.current
    val bitmap by produceState<Bitmap?>(initialValue = null, model) {
        value = withContext(Dispatchers.IO) {
            val retriever = MediaMetadataRetriever()
            try {
                when (model) {
                    is Uri -> retriever.setDataSource(context, model)
                    is java.io.File -> retriever.setDataSource(model.absolutePath)
                }
                retriever.getFrameAtTime(1_000_000L, MediaMetadataRetriever.OPTION_CLOSEST_SYNC)
            } catch (_: Exception) { null }
            finally { try { retriever.release() } catch (_: Exception) {} }
        }
    }
    if (bitmap != null) {
        androidx.compose.foundation.Image(
            bitmap = bitmap!!.asImageBitmap(),
            contentDescription = "Thumbnail video",
            contentScale = ContentScale.Crop,
            modifier = modifier
        )
    } else {
        Box(modifier.background(Color(0xFF111827)), contentAlignment = Alignment.Center) {
            Icon(Icons.Default.Videocam, null, tint = Color(0xFFF43F5E), modifier = Modifier.size(42.dp))
        }
    }
}

'''
    s = s[:old_v.start()] + new_v + s[old_v.end():]

if "private fun resultKindLabel" not in s:
    marker = "\nfun formatFileSize(bytes: Long): String"
    helpers = '''private fun resultKindLabel(file: RecoverableFile): String {
    val hay = (file.name + " " + file.originalPath + " " + file.mimeType).lowercase()
    return when {
        hay.contains("screenshot") || hay.contains("screen_shot") || hay.contains("screen-shot") -> "SCREENSHOT"
        hay.contains("screen recorder") || hay.contains("screen_recorder") || hay.contains("screenrecord") -> "SCREEN RECORDER"
        hay.contains("dcim/camera") || hay.contains("/camera/") || hay.contains("camera_") -> "CAMERA"
        file.category == ScanCategory.VIDEOS -> "VIDEO"
        file.category == ScanCategory.PHOTOS -> "FOTO"
        hay.contains("audio") || hay.contains("music") || hay.contains("record") -> "AUDIO"
        hay.contains(".pdf") || hay.contains(".doc") || hay.contains(".xls") || hay.contains("document") -> "DOKUMEN"
        else -> file.extension.uppercase().ifBlank { "FILE" }
    }
}

private fun sourceLabelForResult(file: RecoverableFile): String {
    val p = file.originalPath
    return when {
        p.contains("Screenshots", true) -> "Screenshots"
        p.contains("ScreenRecorder", true) || p.contains("Screen Record", true) -> "Screen Recorder"
        p.contains("DCIM/Camera", true) -> "Camera"
        file.source.name == "HIDDEN_CACHE" -> "Cache / Thumbnail"
        file.source.name == "FILE_CARVING" -> "File Carving"
        file.source.name == "LOST_DIR" -> "LOST.DIR"
        else -> file.source.name
    }
}

private fun previewCategoryIcon(category: ScanCategory) = when (category) {
    ScanCategory.PHOTOS -> Icons.Default.Image
    ScanCategory.VIDEOS -> Icons.Default.Videocam
    else -> Icons.Default.InsertDriveFile
}

private fun previewCategoryColor(category: ScanCategory) = when (category) {
    ScanCategory.PHOTOS -> CyanLight
    ScanCategory.VIDEOS -> Color(0xFFF43F5E)
    else -> TextSecondary
}

'''
    s = s.replace(marker, "\n" + helpers + "fun formatFileSize(bytes: Long): String", 1)

if "Temuan berdasarkan kategori" not in s:
    marker = "LazyVerticalGrid("
    idx = s.find(marker)
    if idx >= 0:
        summary = '''Column(modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp)) {
    Text("Temuan berdasarkan kategori", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 15.sp)
    Spacer(Modifier.height(8.dp))
    val resultKinds = listOf("SCREENSHOT", "SCREEN RECORDER", "CAMERA", "FOTO", "VIDEO", "AUDIO", "DOKUMEN")
    resultKinds.chunked(2).forEach { row ->
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            row.forEach { kind ->
                val count = filteredFiles.count { resultKindLabel(it) == kind }
                Surface(
                    color = DarkSurface,
                    shape = RoundedCornerShape(10.dp),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFF1E293B)),
                    modifier = Modifier.weight(1f)
                ) {
                    Column(Modifier.padding(10.dp)) {
                        Text(kind, color = CyanLight, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                        Text("\$count temuan", color = Color.White, fontSize = 13.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
        Spacer(Modifier.height(6.dp))
    }
}
'''
        s = s[:idx] + summary + s[idx:]

p.write_text(s)
print("Post-processing media thumbnails and result categories")
