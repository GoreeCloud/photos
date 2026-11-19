package com.goreecloud.photos

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class AlbumValidationTest {
    private val id = "00000000-0000-4000-8000-000000000042"

    @Test fun acceptsCanonicalUuid() {
        assertEquals(id, canonicalLibraryId(id))
    }

    @Test fun rejectsUnexpectedRoutes() {
        listOf(
            "../unsafe", "123", "ABCDEF00-0000-4000-8000-000000000042",
            "00000000-0000-4000-8000-000000000042/original",
            "",
        ).forEach { candidate ->
            assertThrows(IllegalArgumentException::class.java) {
                canonicalLibraryId(candidate)
            }
        }
    }

    @Test fun validatesAlbumNamesWithBoundaryLengths() {
        assertEquals("Family album", validAlbumName("  Family album  "))
        assertEquals("a".repeat(100), validAlbumName("a".repeat(100)))
    }

    @Test fun rejectsBlankAndOversizedAlbumNames() {
        listOf("", "    ", "a".repeat(101)).forEach { candidate ->
            assertThrows(IllegalArgumentException::class.java) {
                validAlbumName(candidate)
            }
        }
    }
}
