<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Manejar preflight OPTIONS request
if ($_SERVER['REQUEST_METHOD'] == 'OPTIONS') {
    exit(0);
}

// Solo aceptar GET requests
if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    http_response_code(405);
    echo json_encode(['error' => 'Solo se permiten requests GET']);
    exit;
}

// Archivo donde se almacenan los datos
$dataFile = 'emg_data.json';

try {
    // Verificar si el archivo existe
    if (!file_exists($dataFile)) {
        echo json_encode([
            'status' => 'success',
            'message' => 'No hay datos disponibles',
            'data' => [],
            'total_batches' => 0,
            'timestamp' => date('c')
        ]);
        exit;
    }
    
    // Leer datos del archivo
    $fileContent = file_get_contents($dataFile);
    
    if ($fileContent === false) {
        throw new Exception('Error al leer archivo de datos');
    }
    
    if (empty(trim($fileContent))) {
        echo json_encode([
            'status' => 'success',
            'message' => 'Archivo de datos vacío',
            'data' => [],
            'total_batches' => 0,
            'timestamp' => date('c')
        ]);
        exit;
    }
    
    $data = json_decode($fileContent, true);
    
    if ($data === null) {
        throw new Exception('Error al decodificar datos JSON');
    }
    
    // Parámetros opcionales
    $limit = isset($_GET['limit']) ? intval($_GET['limit']) : null;
    $latest = isset($_GET['latest']) ? filter_var($_GET['latest'], FILTER_VALIDATE_BOOLEAN) : false;
    
    // Aplicar límite si se especifica
    if ($limit && $limit > 0) {
        if ($latest) {
            // Obtener los últimos N lotes
            $data = array_slice($data, -$limit);
        } else {
            // Obtener los primeros N lotes
            $data = array_slice($data, 0, $limit);
        }
    }
    
    // Calcular estadísticas básicas
    $totalSamples = 0;
    $lastTimestamp = null;
    $firstTimestamp = null;
    
    if (!empty($data)) {
        foreach ($data as $batch) {
            if (isset($batch['samples'])) {
                $totalSamples += count($batch['samples']);
            }
        }
        
        $firstTimestamp = $data[0]['timestamp'] ?? null;
        $lastTimestamp = end($data)['timestamp'] ?? null;
    }
    
    // Respuesta exitosa
    echo json_encode([
        'status' => 'success',
        'message' => 'Datos recuperados exitosamente',
        'data' => $data,
        'total_batches' => count($data),
        'total_samples' => $totalSamples,
        'first_timestamp' => $firstTimestamp,
        'last_timestamp' => $lastTimestamp,
        'file_size' => filesize($dataFile),
        'timestamp' => date('c')
    ]);
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'status' => 'error',
        'message' => $e->getMessage(),
        'timestamp' => date('c')
    ]);
}
?>