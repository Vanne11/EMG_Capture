<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Manejar preflight OPTIONS request
if ($_SERVER['REQUEST_METHOD'] == 'OPTIONS') {
    exit(0);
}

// Solo aceptar POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Solo se permiten requests POST']);
    exit;
}

// Archivo donde se almacenan los datos
$dataFile = 'emg_data.json';

try {
    // Leer datos JSON del request
    $input = file_get_contents('php://input');
    $data = json_decode($input, true);
    
    if ($data === null) {
        throw new Exception('Datos JSON inválidos');
    }
    
    // Validar estructura básica
    if (!isset($data['timestamp']) || !isset($data['samples'])) {
        throw new Exception('Estructura de datos inválida');
    }
    
    // Leer datos existentes o crear array vacío
    $existingData = [];
    if (file_exists($dataFile)) {
        $fileContent = file_get_contents($dataFile);
        if ($fileContent !== false && !empty(trim($fileContent))) {
            $existingData = json_decode($fileContent, true);
            if ($existingData === null) {
                $existingData = [];
            }
        }
    }
    
    // Agregar timestamp del servidor
    $data['server_timestamp'] = date('c');
    $data['server_time_ms'] = round(microtime(true) * 1000);
    
    // Agregar los nuevos datos
    $existingData[] = $data;
    
    // Limitar a los últimos 1000 lotes para evitar archivos muy grandes
    if (count($existingData) > 1000) {
        $existingData = array_slice($existingData, -1000);
    }
    
    // Guardar datos actualizados
    $result = file_put_contents($dataFile, json_encode($existingData, JSON_PRETTY_PRINT));
    
    if ($result === false) {
        throw new Exception('Error al guardar datos en archivo');
    }
    
    // Respuesta exitosa
    echo json_encode([
        'status' => 'success',
        'message' => 'Datos recibidos y guardados',
        'samples_received' => count($data['samples']),
        'total_batches' => count($existingData),
        'timestamp' => date('c')
    ]);
    
} catch (Exception $e) {
    http_response_code(400);
    echo json_encode([
        'status' => 'error',
        'message' => $e->getMessage(),
        'timestamp' => date('c')
    ]);
}
?>