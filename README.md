# Server REST (testing)

* launch server REST : `./server_rest.py localhost 8080`
* start experiment : `curl -X POST -H "Content-Type: multipart/form-data" http://localhost:8080/exp/start/123/clochette -F "firmware=@idle.elf" -F "profile=@tata.json"`
* flash open node : `curl -X POST -H "Content-Type: multipart/form-data" http://localhost:8080/open/flash -F "firmware=@stop.hex"`
