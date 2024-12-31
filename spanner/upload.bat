call secrets.bat
pscp -l klm -pw %passwd% ..\weather_daq\*.py klm@rpi4b-weather:weather/weather_daq/
