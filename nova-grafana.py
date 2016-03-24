#!/usr/bin/python
#coding:utf-8
import requests
import json
import time


def get_token(ip='172.16.69.60', tenantName='admin', username='admin', password='Welcome123'):
    """
    Hàm sử dụng để lấy token
    :param ip: ip của node Controller
    :param tenantName: admin
    :param username: admin
    :param password: Welcome123
    :return:
    """

    try:
        url = 'http://%s:35357/v2.0/tokens' %ip
        headers = {'Content-Type':'application/json'}
        data = {"auth": {"tenantName":"%s" %tenantName,"passwordCredentials":{"username":"%s" %username,"password":"%s" %password}}}

        req = requests.post(url,json.dumps(data),headers = headers)
        response = req.json()
        token = response['access']['token']['id']
        return token
    except Exception,e:
        print e


def create_vm(vm_name, ip='172.16.69.60', tenant_id='642f774100e148edbb5786a368605361',
                image_id='bcfac2c7-60e9-440b-91a9-4d1a7aa82180', flavor_id=1,
                network_id='bb878a72-6886-469c-be58-2bd86fee0425'):
    """
    Hàm tạo máy ảo
    :param vm_name:
    :param ip: IP của node controller
    :param tenant_id: ID của tenant, cần phát triển hàm lấy tenant id
    :param image_id: ID của image
    :param flavor_id: ID của flavor
    :param network_id: ID của network
    :return: ID của VM mới được tạo ra
    """

    try:
        url = 'http://%s:8774/v2/%s/servers' %(ip, tenant_id)
        token = get_token()
        headers = {'X-Auth-Token': token, 'Content-Type':'application/json'}
        data = {"server": {"name": vm_name, "imageRef": image_id, "flavorRef": flavor_id, "max_count": 1, "min_count": 1, "networks": [{"uuid": network_id}]}}
        req = requests.post(url,json.dumps(data), headers = headers)
        if req.status_code != 202:
            print "Loi trong qua trinh tao may ao"
            print "Ma HTTP phan hoi: ", req.status_code
            exit()
        else:
            # Get VM ID
            response = req.json()
            vm_id = response['server']['id']
            print "Tao may ao %s thanh cong, id: %s" %(vm_name, vm_id)
            return vm_id
    except Exception, e:
        print(e)


def get_vm_info(vm_id, ip='172.16.69.60',tenant_id='642f774100e148edbb5786a368605361'):
    """
    hàm lấy thông tin của máy ảo
    :param vm_id: ID của máy ảo cần lấy thông tin
    :param ip: IP của node controller
    :param tenant_id: id của tennant
    :return: Lấy địa chỉa MAC của card mạng đầu tiên gắn vào máy ảo, cần cải tiến hàm này để lấy được nhiều địa chỉ hơn
    """

    try:
        token = get_token()
        url = 'http://%s:8774/v2/%s/servers/%s' %(ip,tenant_id,vm_id)
        headers = {'X-Auth-Token': token, 'Content-Type':'application/json'}
        req = requests.get(url, headers = headers)
        if req.status_code != 200:
            print "Loi trong qua trinh xuat thong tin may ao"
            exit()
        else:
            response = req.json()
            mac_add = response['server']['addresses']['EXT1'][0]['OS-EXT-IPS-MAC:mac_addr']
            return mac_add
    except Exception, e:
        print(e)


def create_dashboard(vm_id, mac_addr, ip_gra='172.16.69.220',
                     token_gra='eyJrIjoiY1Q2Y2ZQSjVsRVM0WWRndFdZQTdCekhjcFFsY25XbzAiLCJuIjoiZHVjbmMiLCJpZCI6MX0='):
    """
    Hàm sử dụng để tạo dashboard trên Grafana
    :param ip_gra: IP của máy chủ Grafana
    :param token_gra: token để thao tác với máy chủ
    :param vm_id: ID của máy ảo
    :param mac_addr: Địa chỉ MAC của máy ảo lấy ở bước trên
    :return:
    """

    # Create grafana dashboard
    new_dashboard = {
      "dashboard": {
        "id": None,
        "title": "%s" %vm_id,
        "timezone": "browser",
      "hideControls": False,
      "sharedCrosshair": False,
      "rows": [
        {
          "collapse": False,
          "editable": False,
          "height": "250px",
          "panels": [
            {
              "aliasColors": {},
              "bars": False,
              "datasource": "Duc-Graphite",
              "editable": False,
              "error": False,
              "fill": 1,
              "grid": {
                "leftLogBase": 1,
                "leftMax": None,
                "leftMin": None,
                "rightLogBase": 1,
                "rightMax": None,
                "rightMin": None,
                "threshold1": None,
                "threshold1Color": "rgba(216, 200, 27, 0.27)",
                "threshold2": None,
                "threshold2Color": "rgba(234, 112, 112, 0.22)"
              },
              "id": 1,
              "isNew": True,
              "legend": {
                "avg": True,
                "current": True,
                "max": True,
                "min": True,
                "show": True,
                "total": False,
                "values": False
              },
              "lines": True,
              "linewidth": 2,
              "links": [],
              "NonePointMode": "connected",
              "percentage": False,
              "pointradius": 5,
              "points": False,
              "renderer": "flot",
              "seriesOverrides": [],
              "span": 12,
              "stack": False,
              "steppedLine": False,
              "targets": [
                {
                  "refId": "A",
                  "target": "vm.%s.metric.libvirt.virt_cpu_total" %vm_id
                }
              ],
              "timeFrom": None,
              "timeShift": None,
              "title": "CPU",
              "tooltip": {
                "shared": True,
                "value_type": "cumulative"
              },
              "type": "graph",
              "x-axis": True,
              "y-axis": True,
              "y_formats": [
                "short",
                "short"
              ]
            }
          ],
          "title": "Row"
        },
        {
          "collapse": False,
          "editable": False,
          "height": "250px",
          "panels": [
            {
              "aliasColors": {},
              "bars": False,
              "datasource": "Duc-Graphite",
              "editable": True,
              "error": False,
              "fill": 1,
              "grid": {
                "leftLogBase": 1,
                "leftMax": None,
                "leftMin": None,
                "rightLogBase": 1,
                "rightMax": None,
                "rightMin": None,
                "threshold1": None,
                "threshold1Color": "rgba(216, 200, 27, 0.27)",
                "threshold2": None,
                "threshold2Color": "rgba(234, 112, 112, 0.22)"
              },
              "id": 2,
              "isNew": True,
              "legend": {
                "avg": True,
                "current": True,
                "max": True,
                "min": True,
                "show": True,
                "total": False,
                "values": False
              },
              "lines": True,
              "linewidth": 2,
              "links": [],
              "NonePointMode": "connected",
              "percentage": False,
              "pointradius": 5,
              "points": False,
              "renderer": "flot",
              "seriesOverrides": [],
              "span": 12,
              "stack": False,
              "steppedLine": False,
              "targets": [
                {
                  "refId": "A",
                  "target": "vm.%s.metric.libvirt.memory-total" %vm_id
                }
              ],
              "timeFrom": None,
              "timeShift": None,
              "title": "RAM",
              "tooltip": {
                "shared": True,
                "value_type": "cumulative"
              },
              "type": "graph",
              "x-axis": True,
              "y-axis": True,
              "y_formats": [
                "short",
                "short"
              ]
            }
          ],
          "title": "New row"
        },
        {
          "collapse": False,
          "editable": True,
          "height": "250px",
          "panels": [
            {
              "aliasColors": {},
              "bars": False,
              "datasource": "Duc-Graphite",
              "editable": True,
              "error": False,
              "fill": 1,
              "grid": {
                "leftLogBase": 1,
                "leftMax": None,
                "leftMin": None,
                "rightLogBase": 1,
                "rightMax": None,
                "rightMin": None,
                "threshold1": None,
                "threshold1Color": "rgba(216, 200, 27, 0.27)",
                "threshold2": None,
                "threshold2Color": "rgba(234, 112, 112, 0.22)"
              },
              "id": 3,
              "isNew": True,
              "legend": {
                "avg": True,
                "current": True,
                "max": True,
                "min": True,
                "show": True,
                "total": False,
                "values": False
              },
              "lines": True,
              "linewidth": 2,
              "links": [],
              "NonePointMode": "connected",
              "percentage": False,
              "pointradius": 5,
              "points": False,
              "renderer": "flot",
              "seriesOverrides": [],
              "span": 12,
              "stack": False,
              "steppedLine": False,
              "targets": [
                {
                  "refId": "A",
                  "target": "vm.%s.metric.libvirt.if_packets-%s.*" %(vm_id, mac_addr)
                }
              ],
              "timeFrom": None,
              "timeShift": None,
              "title": "Network",
              "tooltip": {
                "shared": True,
                "value_type": "cumulative"
              },
              "type": "graph",
              "x-axis": True,
              "y-axis": True,
              "y_formats": [
                "short",
                "short"
              ]
            }
          ],
          "title": "New row"
        }
      ],
      "time": {
        "from": "now-6h",
        "to": "now"
      },
      "timepicker": {
        "refresh_intervals": [
          "30s",
          "1m",
          "5m",
          "15m",
          "30m",
          "1h",
          "2h",
          "1d"
        ],
        "time_options": [
          "5m",
          "15m",
          "1h",
          "6h",
          "12h",
          "24h",
          "2d",
          "7d",
          "30d"
        ]
      },
      "templating": {
        "list": []
      },
      "annotations": {
        "list": []
      },
        "schemaVersion": 6,
        "version": 0
      },
      "overwrite": False
    }

    try:
        url = 'http://%s:3000/api/dashboards/db' % ip_gra
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Bearer %s' % token_gra}

        req = requests.post(url,json.dumps(new_dashboard), headers=headers)
        if req.status_code != 200:
            print "Loi trong qua trinh tao Grafana dashboard"
            exit()
        else:
            print "Tao Grafana dashboard thanh cong!"
            response = req.json()
    except Exception,e:
        print(e)


def get_grafana_panel_url(vm_id, ip_gra='172.16.69.220'):
    """
    Hàm lấy ra URL của panel CPU, RAM, Network của mỗi instance
    :param vm_id: id của máy ảo = id của Grafana dashboard
    :param ip_gra: ip của máy chủ Grafana
    :return: URL
    """

    grafana_url_list = []
    url_cpu = 'http://%s:3000/dashboard-solo/db/%s?panelId=1&fullscreen' % (ip_gra, vm_id)
    url_ram = 'http://%s:3000/dashboard-solo/db/%s?panelId=2&fullscreen' % (ip_gra, vm_id)
    url_net = 'http://%s:3000/dashboard-solo/db/%s?panelId=3&fullscreen' % (ip_gra, vm_id)

    grafana_url_list.append({vm_id : [url_cpu, url_net, url_ram]})

    return grafana_url_list


def main():
    vm_id = create_vm('congtt')
    time.sleep(10)
    mac_addr = get_vm_info(vm_id)
    print "Dia chi MAC cua may ao:", mac_addr
    create_dashboard(vm_id, mac_addr)


if __name__ == '__main__':
    main()
