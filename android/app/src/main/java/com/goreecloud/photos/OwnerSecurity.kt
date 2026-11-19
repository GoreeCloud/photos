package com.goreecloud.photos

/** Validation shared by owner-authenticated Android security actions. */
internal fun validateOwnerSecret(current: String) {
    require(current.length in 1..1024) {
        "Enter the current library password (maximum 1024 characters)"
    }
}

internal fun validateOwnerRotation(current: String, replacement: String, confirmation: String) {
    validateOwnerSecret(current)
    require(replacement.length in 12..1024) {
        "New password must contain 12 to 1024 characters"
    }
    require(replacement != current) { "Choose a different new password" }
    require(replacement == confirmation) { "New password and confirmation do not match" }
}
