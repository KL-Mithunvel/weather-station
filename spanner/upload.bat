call secrets.bat
pscp -l klm -pw %passwd% ..\weather_daq\*.* klm@rpi4b-weather:weather/weather_daq/
pscp -l klm -pw %passwd% ..\weather_web\*.* klm@rpi4b-weather:weather/weather_web/