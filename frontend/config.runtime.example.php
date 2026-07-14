<?php
/**
 * Copy this file to config.runtime.php on MilesWeb and set FINREVIEW_API_URL
 * in your hosting environment, cPanel, or a private server-side config include.
 *
 * This keeps the real backend URL out of Git while still giving browser
 * JavaScript the public API origin it must call.
 */
header('Content-Type: application/javascript; charset=utf-8');

$apiUrl = getenv('FINREVIEW_API_URL') ?: '';

if ($apiUrl === '') {
    echo "console.warn('FINREVIEW_API_URL is not configured. Falling back to frontend default.');";
    exit;
}

echo 'window.FINREVIEW_API_URL = ' . json_encode(rtrim($apiUrl, '/')) . ';';