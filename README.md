To build a Docker image:

    docker build -t symlog .
  
To run the tuple explosion example:

    docker run -it --name tup-explosion symlog bash
    ./run_tup_explosion_example.sh
