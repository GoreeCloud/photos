package com.goreecloud.photos

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp

@Composable
internal fun OwnerSecurityDialog(
    busy: Boolean,
    error: String,
    onDismiss: () -> Unit,
    onRotate: (String, String, String) -> Unit,
    onRevoke: (String) -> Unit,
) {
    var current by remember { mutableStateOf("") }
    var replacement by remember { mutableStateOf("") }
    var confirmation by remember { mutableStateOf("") }
    var validationError by remember { mutableStateOf("") }

    fun wipe() {
        current = ""
        replacement = ""
        confirmation = ""
        validationError = ""
    }

    AlertDialog(
        onDismissRequest = { if (!busy) { wipe(); onDismiss() } },
        title = { Text("Library security") },
        text = {
            Column(
                modifier = Modifier.verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Text("This is a private, single-library credential. Both actions sign out every device.")
                OutlinedTextField(
                    value = current,
                    onValueChange = { if (it.length <= 1024) { current = it; validationError = "" } },
                    label = { Text("Current password") },
                    visualTransformation = PasswordVisualTransformation(),
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                OutlinedTextField(
                    value = replacement,
                    onValueChange = { if (it.length <= 1024) { replacement = it; validationError = "" } },
                    label = { Text("New password (12-1024 characters)") },
                    visualTransformation = PasswordVisualTransformation(),
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                OutlinedTextField(
                    value = confirmation,
                    onValueChange = { if (it.length <= 1024) { confirmation = it; validationError = "" } },
                    label = { Text("Confirm new password") },
                    visualTransformation = PasswordVisualTransformation(),
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                val visibleError = validationError.ifEmpty { error }
                if (visibleError.isNotEmpty()) {
                    Text(
                        visibleError,
                        modifier = Modifier.semantics { liveRegion = LiveRegionMode.Assertive },
                    )
                }
            }
        },
        confirmButton = {
            // Keep all actions in one vertical layout. Using separate Material
            // confirm/dismiss slots overlapped Revoke and Cancel on Android 16.
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(4.dp),
            ) {
                TextButton(
                    modifier = Modifier.fillMaxWidth(),
                    enabled = !busy && current.isNotEmpty() &&
                        replacement.isNotEmpty() && confirmation.isNotEmpty(),
                    onClick = {
                        try {
                            validateOwnerRotation(current, replacement, confirmation)
                        } catch (invalid: IllegalArgumentException) {
                            validationError = invalid.message ?: "Invalid password change"
                            return@TextButton
                        }
                        val old = current
                        val next = replacement
                        val confirm = confirmation
                        wipe()
                        onRotate(old, next, confirm)
                    },
                ) { Text("Change password and sign out devices") }
                TextButton(
                    modifier = Modifier.fillMaxWidth(),
                    enabled = !busy && current.isNotEmpty(),
                    onClick = {
                        val old = current
                        wipe()
                        onRevoke(old)
                    },
                ) { Text("Sign out devices; keep password") }
                TextButton(
                    modifier = Modifier.fillMaxWidth(),
                    enabled = !busy,
                    onClick = { wipe(); onDismiss() },
                ) { Text("Cancel") }
            }
        },
    )
}
