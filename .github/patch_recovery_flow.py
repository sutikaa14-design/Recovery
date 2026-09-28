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
