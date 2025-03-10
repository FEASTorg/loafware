# Planning

## Summary

A Raspberry Pi 4 hosts a modular Python control service that communicates with multiple I2C devices through dedicated driver modules. Sensor data is periodically polled and stored in InfluxDB, while Grafana provides real-time visualizations via local dashboards. A REST API facilitates remote command dispatch to alter device states or behaviors. The entire system is containerized using Docker Compose for streamlined deployment and extensibility. After initial setup, it runs locally—either via a local router or with the Raspberry Pi as an access point—ensuring browser-based access without an internet connection. This design enables rapid setup and modification, making it straightforward to add new devices or update dashboards for process control applications such as bioreactors.
