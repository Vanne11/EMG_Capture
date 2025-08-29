<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Manejar preflight OPTIONS request
if ($_SERVER['REQUEST_METHOD'] == 'OPTIONS') {
    exit(0);
}

// Aceptar tanto POST como GET para flexibilidad
if (!in_array($_SERVER['REQUEST_METHOD'], ['POST', 'GET'])) {
    http_response_code(405);
    echo json_encode(['error' => 'Solo se permiten requests POST o GET']);
    exit;
}

// Archivo donde se almacenan los datos
$dataFile = 'emg_data.json';

try {
    // Verificar si el archivo existe
    $fileExists = file_exists($dataFile);
    $previousSize = 0;
    $deletedBatches = 0;
    
    if ($fileExists) {
        // Obtener información del archivo antes de borrarlo
        $fileContent = file_get_contents($dataFile);
        if ($fileContent !== false && !empty(trim($fileContent))) {
            $existingData = json_decode($fileContent, true);
            if ($existingData !== null && is_array($existingData)) {
                $deletedBatches = count($existingData);
                $previousSize = filesize($dataFile);
            }
        }
        
        // Borrar el archivo
        $result = unlink($dataFile);
        
        if (!$result) {
            throw new Exception('Error al borrar el archivo de datos');
        }
        
        $message = "Datos borrados exitosamente";
    } else {
        $message = "No había datos para borrar";
    }
    
    // Respuesta exitosa
    echo json_encode([
        'status' => 'success',
        'message' => $message,
        'file_existed' => $fileExists,
        'deleted_batches' => $deletedBatches,
        'previous_file_size' => $previousSize,
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