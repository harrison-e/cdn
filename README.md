# Content Delivery Network (CDN)
*implemented for CS4700 at NU*


This repository contains the necessary bits and pieces for a HTML CDN. That is, a collection of scripts to deploy, run, and stop a CDN on a provided list of HTTP and DNS hosts.


The DNS server is not necessary to use the HTTP servers, but can be used for custom DNS redirection from a given hostname to any of the provided edge servers.


## Usage
To configure the hostnames, first fill out the necessary files in [the .config directory](./.config/). After configuration, simply run the following commands, **in order**:

- [`./deployCDN [-h] -u USERNAME -i IDENTITY_FILE`](./deployCDN)
- [`./runCDN [-h] -p PORT -o ORIGIN -n NAME -u USERNAME -i IDENTITY_FILE [-v]`](./runCDN)
- [`./stopCDN [-h] [-p PORT] [-o ORIGIN] [-n NAME] -u USERNAME -i IDENTITY_FILE`](./stopCDN)


Where
- `USERNAME` and `IDENTITY_FILE` (aka private key) are used to log into machines running the server code using `ssh` (assuming all servers allow that username and identity file)
- `ORIGIN` is the address to the CDN origin server, which serves all HTML content via HTTP requests
- `NAME` is the name that the DNS server will resolve as one of the edge servers 
- `-v` runs the servers in verbose mode 
- and `-h` describes usage

