package com.goreecloud.photos

import org.junit.Assert.assertThrows
import org.junit.Test

class OwnerSecurityTest {
    @Test fun acceptsCurrentSecretAndValidDifferentReplacement() {
        validateOwnerSecret("synthetic-current-2026")
        validateOwnerRotation(
            "synthetic-current-2026",
            "synthetic-next-pass-2026",
            "synthetic-next-pass-2026",
        )
    }

    @Test fun rejectsInvalidOwnerSecrets() {
        for (value in listOf("", "x".repeat(1025))) {
            assertThrows(IllegalArgumentException::class.java) {
                validateOwnerSecret(value)
            }
        }
    }

    @Test fun rejectsInvalidReplacementOrConfirmation() {
        val current = "synthetic-current-password"
        for ((replacement, confirmation) in listOf(
            "" to "", "short" to "short",
            current to current,
            "new-valid-pass-2026" to "not-the-same-secret",
            "z".repeat(1025) to "z".repeat(1025),
        )) {
            assertThrows(IllegalArgumentException::class.java) {
                validateOwnerRotation(current, replacement, confirmation)
            }
        }
    }
}
