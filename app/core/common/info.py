WAY_TO_FIND_SERVER_LOG = """
Please check the error details in Chat2Graph log:
your_path% bin/restart.sh
... ...
Init application: Chat2Graph
Init the Leader agent
Init the Expert agents
  ____ _           _   ____   ____                 _     
 / ___| |__   __ _| |_|___ \ / ___|_ __ __ _ _ __ | |__  
| |   | '_ \ / _` | __| __) | |  _| '__/ _` | '_ \| '_ \ 
| |___| | | | (_| | |_ / __/| |_| | | | (_| | |_) | | | |
 \____|_| |_|\__,_|\__|_____|\____|_|  \__,_| .__/|_| |_|
                                            |_|          

 * Serving Flask app 'bootstrap'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5010
 * Running on http://30.239.2.244:5010
Detail logs in /Users/kuda/.chat2graph/logs/server_***timestamp***.log <<<< find the log path here
"""  # noqa: E501
