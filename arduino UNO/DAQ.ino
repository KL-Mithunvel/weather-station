#include "SparkFun_Weather_Meter_Kit_Arduino_Library.h"

 int windDirectionPin = A0;
 int windSpeedPin = 3;
 int rainfallPin = 2;


SFEWeatherMeterKit weatherMeterKit(windDirectionPin, windSpeedPin, rainfallPin);

void setup()
{
    
    Serial.begin(115200);

    SFEWeatherMeterKitCalibrationParams calibrationParams = weatherMeterKit.getCalibrationParams();
    
    calibrationParams.vaneADCValues[WMK_ANGLE_0_0] = 785;
    calibrationParams.vaneADCValues[WMK_ANGLE_22_5] = 405;
    calibrationParams.vaneADCValues[WMK_ANGLE_45_0] = 460;
calibrationParams.vaneADCValues[WMK_ANGLE_67_5] = 26;                               `   ``  `                   
    calibrationParams.vaneADCValues[WMK_ANGLE_90_0] = 93;
    calibrationParams.vaneADCValues[WMK_ANGLE_112_5] = 65;
    calibrationParams.vaneADCValues[WMK_ANGLE_135_0] = 184;
    calibrationParams.vaneADCValues[WMK_ANGLE_157_5] = 126;
    calibrationParams.vaneADCValues[WMK_ANGLE_180_0] = 287;
    calibrationParams.vaneADCValues[WMK_ANGLE_202_5] = 244;
    calibrationParams.vaneADCValues[WMK_ANGLE_225_0] = 629;
    calibrationParams.vaneADCValues[WMK_ANGLE_247_5] = 598;
    calibrationParams.vaneADCValues[WMK_ANGLE_270_0] = 944;
    calibrationParams.vaneADCValues[WMK_ANGLE_292_5] = 826;
    calibrationParams.vaneADCValues[WMK_ANGLE_315_0] = 886;
    calibrationParams.vaneADCValues[WMK_ANGLE_337_5] = 702;


    calibrationParams.mmPerRainfallCount = 0.2794;
    calibrationParams.minMillisPerRainfall = 100;
    calibrationParams.kphPerCountPerSec = 2.4;

    calibrationParams.windSpeedMeasurementPeriodMillis = 1000;


    weatherMeterKit.setCalibrationParams(calibrationParams);
    weatherMeterKit.begin();
}

void loop()
{
//"Wind direction (degrees)
    Serial.print(weatherMeterKit.getWindDirection(), 1);
    Serial.print(",");
    //"Wind speed (kph)
    Serial.print(weatherMeterKit.getWindSpeed(), 1);
    Serial.print(",");
    //"Total rainfall (mm): "
    Serial.println(weatherMeterKit.getTotalRainfall(), 1);
    // Only print once per second
    delay(1000);
}
