from flask import render_template_string


def wrap_html(s):
    return render_template_string("<head><style>" + """"table {
      border-collapse: collapse;
      width: 100%;
      text-overflow: ellipsis;
      border: 1px solid black;
    }
    
    th, td {
      text-align: left;
      padding: 8px;
      text-overflow: ellipsis;
      width: 20%;
    }
    
    tr:nth-child(even){background-color: #f2f2f2}
    
    th {
      background-color: #4CAF50;
      color: white;
    }
    
    """ + "</style></head>" + s)
