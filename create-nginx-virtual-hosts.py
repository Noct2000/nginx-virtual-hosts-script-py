#!/usr/bin/env python3

import subprocess
import os
import sys
import socket

def install_package(package_name):
    subprocess.run(
        ['sudo', 'apt-get', 'update'],
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )
    subprocess.run(
        ['sudo', 'apt-get', 'install', '-y', package_name],
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )

def create_virtual_host(hostname):
    print(f"Creating: {hostname} virtual host")
    
    # Prepare host config
    base_virtual_host_config = f"""
    # Virtual Host configuration for {hostname}
    #
    # You can move that to a different file under sites-available/ and symlink that
    # to sites-enabled/ to enable it.
    #
    server {{
            listen 80;
            listen [::]:80;

            server_name {hostname};

            root /var/www/{hostname}/html;
            index index.html;

            location / {{
                    try_files $uri $uri/ =404;
            }}
    }}
    """
    
    # Write config to /etc/nginx/sites-available/{hostname}
    with open(f"/etc/nginx/sites-available/{hostname}", 'w') as config_file:
        config_file.write(base_virtual_host_config)

    print("Success")
    
    # Create base page for {hostname} virtual host
    web_page = f"""
    <html>
        <body>
            Hello from {hostname}
        </body>
    </html>
    """
    
    # Create directory and write index.html
    os.makedirs(f"/var/www/{hostname}/html", exist_ok=True)
    with open(f"/var/www/{hostname}/html/index.html", 'w') as index_file:
        index_file.write(web_page)

    print("Success")

    # Change web page owner
    subprocess.run(
        ['sudo', 'chown', '-R', f'{os.getlogin()}:{os.getlogin()}', f'/var/www/{hostname}/html'],
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )

    # Make host available
    subprocess.run(
        ['sudo', 'ln', '-s', f'/etc/nginx/sites-available/{hostname}', f'/etc/nginx/sites-enabled/{hostname}'],
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )

def main():
    # Get the arguments from the command-line except the filename
    args = sys.argv[1:]
    args_count = len(args)

    if args_count == 0:
        print("No command-line arguments provided.")
        print("Please enter at least one virtual hostname for nginx")
        print("Example:")
        print("python create-nginx-virtual-hosts.py myhost1.com myhost2.org myhost3.com")
    else:
        # Check if OpenSSH Server is installed
        if b"openssh-server" not in subprocess.check_output(['sudo' ,'dpkg', '-l']):
            print("OpenSSH Server is not installed. Installing...")
            install_package("openssh-server")
        else:
            print("OpenSSH Server is already installed.")

        # Check if Nginx is installed
        if b"nginx" not in subprocess.check_output(['sudo', 'dpkg', '-l']):
            print("Nginx is not installed. Installing...")
            install_package("nginx")
        else:
            print("Nginx is already installed.")

        # Stop nginx
        subprocess.run(['sudo', 'systemctl', 'stop', 'nginx'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Loop through all virtual hostnames
        for arg in args:
            create_virtual_host(arg)

        print("Fix error hash bucket memory")
        subprocess.run(
            ['sudo', 'sed', '-i', 's/# server_names_hash_bucket_size 64;/server_names_hash_bucket_size 64;/', '/etc/nginx/nginx.conf'],
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        print("Success")

        print("Start nginx")
        subprocess.run(
            ['sudo', 'systemctl', 'start', 'nginx'],
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        
        print("Get IP address")
        # Get the host name
        host_name = socket.gethostname()

        # Get the IP address associated with the host name
        ip_address = socket.gethostbyname(host_name)
        print("Success")

        print("Please add the following line to your hosts file:")
        print(f"{ip_address} {' '.join(args)}")
        print("Usual Windows path: \"C:\\Windows\\System32\\drivers\\etc\\hosts\"")
        print("Usual Linux path: \"/etc/hosts\"")

if __name__ == "__main__":
    main()
