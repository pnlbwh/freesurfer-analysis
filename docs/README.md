![](pnl-bwh-hms.png)

Outlier detection tool utilizing FreeSurfer segmentation statistics, built using https://plotly.com/dash/


# Troubleshooting

* `Address already in use`: The error implies that the port mentioned in 
`app.run_server(debug=False, port= 8040, host= 'localhost')` is already in use.

```bash
Traceback (most recent call last):
  File "/data/pnl/soft/pnlpipe3/freesurfer-analysis/scripts/analyze-stats.py", line 170, in <module>
    app.run_server(debug=False, port= 8040, host= 'localhost')
  File "/data/pnl/soft/pnlpipe3/miniconda3/envs/pnlpipe3/lib/python3.6/site-packages/dash/dash.py", line 1509, in run_server
    self.server.run(host=host, port=port, debug=debug, **flask_run_options)
  File "/data/pnl/soft/pnlpipe3/miniconda3/envs/pnlpipe3/lib/python3.6/site-packages/flask/app.py", line 990, in run
    run_simple(host, port, self, **options)
  File "/data/pnl/soft/pnlpipe3/miniconda3/envs/pnlpipe3/lib/python3.6/site-packages/werkzeug/serving.py", line 1052, in run_simple
    inner()
  File "/data/pnl/soft/pnlpipe3/miniconda3/envs/pnlpipe3/lib/python3.6/site-packages/werkzeug/serving.py", line 1005, in inner
    fd=fd,
  File "/data/pnl/soft/pnlpipe3/miniconda3/envs/pnlpipe3/lib/python3.6/site-packages/werkzeug/serving.py", line 848, in make_server
    host, port, app, request_handler, passthrough_errors, ssl_context, fd=fd
  File "/data/pnl/soft/pnlpipe3/miniconda3/envs/pnlpipe3/lib/python3.6/site-packages/werkzeug/serving.py", line 740, in __init__
    HTTPServer.__init__(self, server_address, handler)
  File "/data/pnl/soft/pnlpipe3/miniconda3/envs/pnlpipe3/lib/python3.6/socketserver.py", line 456, in __init__
    self.server_bind()
  File "/data/pnl/soft/pnlpipe3/miniconda3/envs/pnlpipe3/lib/python3.6/http/server.py", line 136, in server_bind
    socketserver.TCPServer.server_bind(self)
  File "/data/pnl/soft/pnlpipe3/miniconda3/envs/pnlpipe3/lib/python3.6/socketserver.py", line 470, in server_bind
    self.socket.bind(self.server_address)
OSError: [Errno 98] Address already in use
```

One way to solve this issue would be to follow 
https://stackoverflow.com/questions/11583562/how-to-kill-a-process-running-on-particular-port-in-linux .
However, if you do not have privilege over that port, you might not be able to stop it from listening. 

In that case, open `scripts/ports.py` and assign another four digit port to the variable reported in the traceback, and try again.

