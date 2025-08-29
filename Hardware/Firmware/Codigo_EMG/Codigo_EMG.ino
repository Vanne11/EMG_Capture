#include <Wire.h>
#include <Adafruit_ADS1X15.h>

// Define los pines SDA y SCL personalizados
#define SDA_PIN 6  // Cambia este número al pin que quieras usar como SDA
#define SCL_PIN 7  // Cambia este número al pin que quieras usar como SCL

Adafruit_ADS1115 ads;  // Instancia del ADS1115

void setup() {
  Serial.begin(9600);
  Serial.println("Iniciando ADS1115 con pines personalizados");
  
  // Inicializar Wire con pines personalizados
  Wire.begin(SDA_PIN, SCL_PIN);
  
  // Iniciar el ADS1115
  if (!ads.begin()) {
    Serial.println("No se pudo inicializar el ADS1115!");
    while (1);
  }
  
  // Configurar el rango de medición (opcional)
  // ads.setGain(GAIN_ONE); // 1x gain = +/- 4.096V
  
  Serial.println("ADS1115 inicializado correctamente!");
}

void loop() {
  // Leer los valores de los diferentes canales
  int16_t adc3;
  

  adc3 = ads.readADC_SingleEnded(3);
  
  // Convertir a voltaje (opcional)

  float volts3 = ads.computeVolts(adc3);
  
  // Imprimir resultados

  Serial.println(adc3); 
  
  delay(10);
}