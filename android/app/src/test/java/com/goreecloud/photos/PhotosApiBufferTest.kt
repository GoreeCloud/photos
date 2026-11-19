package com.goreecloud.photos

import java.io.ByteArrayInputStream
import java.io.IOException
import java.io.InputStream
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class PhotosApiBufferTest {
    @Test fun acceptsExactBoundAndClosesStream() {
        val content = ByteArray(120_000) { (it % 251).toByte() }
        var closed = false
        val stream = object : ByteArrayInputStream(content) {
            override fun close() {
                super.close()
                closed = true
            }
        }
        assertArrayEquals(content, readBounded(stream, 120_000))
        assertTrue("Input must always be closed", closed)
    }

    @Test fun rejectsOversizedResponseBeforeReadCompletion() {
        val content = ByteArray(130_000) { 42 }
        var closed = false
        val stream = object : ByteArrayInputStream(content) {
            override fun close() {
                super.close()
                closed = true
            }
        }
        var threw = false
        try {
            readBounded(stream, 120_000)
        } catch (e: IllegalStateException) {
            threw = e.message?.contains("safe limit") == true
        }
        assertTrue("Oversized response must be rejected", threw)
        assertTrue("Rejected stream must still close", closed)
    }

    @Test fun rejectsInvalidLimits() {
        try {
            readBounded(ByteArrayInputStream(byteArrayOf(1)), 0)
            throw AssertionError("Invalid limit accepted")
        } catch (_: IllegalArgumentException) {
            // Expected.
        }
    }

    @Test fun streamingIoFailuresAreNotSilenced() {
        val stream = object : InputStream() {
            override fun read(): Int = throw IOException("synthetic read failure")
        }
        try {
            readBounded(stream, 1024)
            throw AssertionError("Read failure was swallowed")
        } catch (_: IOException) {
            // Expected.
        }
    }
}
