FROM python:3.9-slim-bullseye

RUN apt update && apt install -y nmap

# Create default user folder
RUN mkdir -p /home/pi

# Install cygnus service
COPY cygnus /home/pi/cygnus
RUN cd /home/pi/cygnus && pip3 install .

LABEL version="0.0.1"
LABEL permissions='\
{\
 "ExposedPorts": {\
   "8000/tcp": {}\
  },\
  "HostConfig": {\
    "Binds":["/root/.config:/root/.config"],\
    "PortBindings": {\
      "8000/tcp": [\
        {\
          "HostPort": ""\
        }\
      ]\
    }\
  }\
}'
LABEL authors='[\
    {\
        "name": "Rustom Jehangir",\
        "email": "rusty@bluerobotics.com"\
    }\
]'
LABEL company='{\
        "about": "",\
        "name": "Blue Robotics",\
        "email": "support@bluerobotics.com"\
    }'
LABEL type="device-integration"
LABEL tags='[\
        "inspection",\
        "sensor"\
    ]'
LABEL readme='https://raw.githubusercontent.com/rjehangir/BlueOS-Cygnus-UT/{tag}/README.md'
LABEL links='{\
        "website": "https://github.com/rjehangir/BlueOS-Cygnus-UT",\
        "support": "https://github.com/rjehangir/BlueOS-Cygnus-UT/issues"\
    }'
LABEL requirements="core >= 1.1"

ENTRYPOINT /home/pi/cygnus/main.py
