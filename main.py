
from flask import Flask, session, render_template, url_for, redirect, request
from flask.ext.bootstrap import Bootstrap

from keystone_api import (get_token, get_tenant_id, get_tenant_list)
from mail import (send_mail,reports)
from neutron_api import (check_neutron_service, get_ports, get_network)
from nova_api import (get_server_list, get_compute_list, get_compute_statistics, check_nova_service, get_tenant_usage)
from cinder_api import (get_volumes_list)

import os
# default Variable
username = None
password = None
tenant_name = 'admin'

hostname = None
error = None

network_public_id = ''
ip_used = 0

app = Flask(__name__)
Bootstrap(app)

# load config from file

app.config.from_pyfile('config.py')

## import config value

keystone_port = app.config['KEYSTONE_PORT']
nova_port = app.config['NOVA_PORT']
neutron_port = app.config['NEUTRON_PORT']
cinder_port = app.config['CINDER_PORT']

## config email
mail_server = app.config['MAIL_SERVER']
mail_server_port = app.config['MAIL_SERVER_PORT']

# your mail
sender = app.config['SENDER']
password_sender = app.config['PASSWORD_SENDER']

#sender = os.environ.get('SENDER')
#password_sender = os.environ.get('PASSWORD_SENDER')

# config neutron
network_public_name = app.config['NETWORK_PUBLIC_NAME']
#network_public_name = os.environ.get('NETWORK_PUBLIC_NAME')

## login to UI use username, password and IP API 

@app.route("/login", methods=['GET', 'POST'])
def login():
    global username
    global password
    global hostname
    global error
    error = request.args.get('error')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hostname = request.form['hostname']
        token = get_token(tenant_name, username, password, hostname, keystone_port)
        print token
        session['logged_in'] = True
        session['token'] = token
        return redirect(url_for("index"))
    return render_template("login.html", error=error)


## logout

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))


## show all service status  in openstack

@app.route("/services")
def services():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    token = session.get('token')
    id_tenant_admin = get_tenant_id(token, hostname, keystone_port, 'admin')
    nova_service = check_nova_service(token=token, tenant_id=id_tenant_admin, username=username, password=password,
                                      hostname=hostname, keystone_port=keystone_port)
    neutron_agents = check_neutron_service(token=token, tenant_id=id_tenant_admin, username=username, password=password,
                                           hostname=hostname, keystone_port=keystone_port)
    print nova_service
    return render_template("services.html", nova_service=nova_service, neutron_agents=neutron_agents)


###show all instance in openstack

@app.route("/instances")
def show_instance():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    token = session.get('token')
    if token != None:
        id_tenant_admin = get_tenant_id(token, hostname, keystone_port, 'admin')
        instances_list = get_server_list(id_tenant_admin, token, hostname, nova_port)
#        grafana_url_list = []
#        for vm_id in
#            url_cpu = 'http://%s:3000/dashboard-solo/db/%s?panelId=1&fullscreen' % (ip_gra, vm_id)
#            url_ram = 'http://%s:3000/dashboard-solo/db/%s?panelId=2&fullscreen' % (ip_gra, vm_id)
#            url_net = 'http://%s:3000/dashboard-solo/db/%s?panelId=3&fullscreen' % (ip_gra, vm_id)

        return render_template("instances.html", instances_list=instances_list, 
                                network_public_name=network_public_name)
    else:
        error = 'Time Out'
        return redirect(url_for('login', error=error))


        ## show resource usage all tenant


@app.route("/tenant")
def tenant_usage():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    token = session.get('token')
    if token != None:
        tenant_list = get_tenant_list(token, hostname, keystone_port)  # get tenant list
        tenant_admin_id = get_tenant_id(token, hostname, keystone_port, 'admin')  # get id tenant admin
        tenant_usage = {}
        all_tenant_usage = []
        for tenant in range(len(tenant_list['tenants'])):
            tenant_usage['name'] = tenant_list['tenants'][tenant]['name']
            tenant_usage['id'] = tenant_list['tenants'][tenant]['id']
            
            tenant_usage_detail = get_tenant_usage(tenant_admin_id, tenant_list['tenants'][tenant]['id'], 
                                                    token,hostname, nova_port)  # get instance in tenant

            if 'server_usages' in tenant_usage_detail['tenant_usage']:
                instances = len(tenant_usage_detail['tenant_usage']['server_usages'])
                vcpus_used = 0
                rams_used = 0
                disks_used = 0
                for instance in range(instances):
                    rams_used = rams_used + tenant_usage_detail['tenant_usage']['server_usages'][instance]['memory_mb']
                    vcpus_used = vcpus_used + tenant_usage_detail['tenant_usage']['server_usages'][instance]['vcpus']
                    disks_used = disks_used + tenant_usage_detail['tenant_usage']['server_usages'][instance]['local_gb']

                tenant_usage['tenant_usage'] = {"instances": instances, "rams_used": rams_used,
                                                "disks_used": disks_used, "vcpus_used": vcpus_used}
            else:
                instances = 0
                vcpus_used = 0
                rams_used = 0
                disks_used = 0
                tenant_usage['tenant_usage'] = {"instances": instances, "rams_used": rams_used,
                                                "disks_used": disks_used, "vcpus_used": vcpus_used}
            all_tenant_usage.append(tenant_usage.copy())
        return render_template("tenant.html", all_tenant_usage=all_tenant_usage)
    else:
        error = 'Time Out'
        return redirect(url_for('login', error=error))

    return render_template("tenant.html")


## index show resource from total compute or each compute

@app.route("/", methods=['GET','POST'])
def index():
    all = True
    alert = None
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    token = session.get('token')
    if token != None:
        if request.method=='POST':

            email = request.form.get('email')
            node = request.args.get('node')          
            cpu_used = int(request.args.get('cpu_used'))
            cpu_total = int(request.args.get('cpu_total'))
            ram_used =int(request.args.get('ram_used'))         
            ram_total = int(request.args.get('ram_total'))          
            hdd_free = int(request.args.get('hdd_free'))
            hdd_total = int(request.args.get('hdd_total'))
            instances = int(request.args.get('instances'))
            if node == "all":
                volumes = int(request.args.get('volumes'))
            else:
                volumes = 0
            alert = reports(node,cpu_used,cpu_total,ram_total,ram_used,
                            hdd_total,hdd_free,instances,volumes,email,mail_server,
                            mail_server_port,sender,password_sender)

        id_tenant_admin = get_tenant_id(token, hostname, keystone_port, 'admin')  # get ID of tenant Admin
        ports = get_ports(token, hostname, neutron_port)  # get all ports details
        networks_list = get_network(token, hostname, neutron_port)  # get all network list
        for net in range(len(networks_list['networks'])):
                if networks_list['networks'][net]['name'] == network_public_name:
                    global network_public_id
                    network_public_id = networks_list['networks'][net]['id'] 

        if request.args.get('show') == 'all':  # display all compute list
            compute_list = []
            list_node = get_compute_list(id_tenant_admin, token, hostname, nova_port)
            for i in range(len(list_node['hypervisors'])):                
                ip_used =0
                info = get_compute_list(id_tenant_admin, token, hostname, nova_port,
                                        str(list_node['hypervisors'][i]['id']))

                compute_name = list_node['hypervisors'][i]['hypervisor_hostname']                
                for ip in range(len(ports['ports'])):
                    if ports['ports'][ip]['network_id'] == network_public_id and ports['ports'][ip]['binding:host_id'] == compute_name:  # if network in instance match with network public
                        ip_used = ip_used + 1
                info['ip_used'] = ip_used
                compute_list.append(info)
                print compute_list
            return render_template("index.html", compute_list=compute_list, 
                                     total=False,alert =alert)
        else:
            ip_used = 0
            for ip in range(len(ports['ports'])):
                if ports['ports'][ip][
                    'network_id'] == network_public_id:  # if network in instance match with network public
                    ip_used = ip_used + 1
            volumes = get_volumes_list(id_tenant_admin, token, hostname, cinder_port)
            compute_list = get_compute_statistics(id_tenant_admin, token, hostname, nova_port)
            return render_template("index.html", compute_list=compute_list, 
                                    ip_used=ip_used, volumes=volumes,total=True,alert = alert)
    else:
        error = 'Time Out'
        return redirect(url_for('login', error=error))
    return render_template('index.html')


## run app

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port,debug=True)
