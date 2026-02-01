#!/usr/local/bin/python

import os
from squirrel.mongo.mongo_connect import MongoUtil
from squirrel.client_model import Client
from squirrel.models_model import Model, Port, SPEED_CAP_MAP
mongo_host = os.environ['MONGO_HOST']
mongo_db_main = os.environ['MONGO_DB_NAME']
SPEED_CAP_LIST_MAP = {'0123459': [SPEED_CAP_MAP[0], SPEED_CAP_MAP[1], SPEED_CAP_MAP[2], SPEED_CAP_MAP[3], SPEED_CAP_MAP[4], SPEED_CAP_MAP[5], SPEED_CAP_MAP[9]], '012345': [SPEED_CAP_MAP[0], SPEED_CAP_MAP[1], SPEED_CAP_MAP[2], SPEED_CAP_MAP[3], SPEED_CAP_MAP[4], SPEED_CAP_MAP[5]], '012': [SPEED_CAP_MAP[0], SPEED_CAP_MAP[1], SPEED_CAP_MAP[2]]}

def add_custom_models_to_collection():
    try:
        container = mongo_host
        client = MongoUtil.mongo_connector()
        client.admin.command('ismaster')
    except Exception as e:
        return 'Error: ' + str(e.message)
    MongoUtil.mongo_connector()

    ap_ecw230_model = Model(type=Model.type_ap, name='ECW230', band='2_4G|5G', category=Model.category_indoor, number='X42', dfs_support_type=['fcc', 'eu'])
    switch_ecs2510fp_model = Model(type=Model.type_switch, name='ECS2510FP', number='RCF', support_poe=True)
    switch_ecs2510fp_model.ports.append(Port(id='1', poe_type=Port.poe_bt_type, speed_cap=['auto', '1Gbps_fdx', '100Mbps_fdx', '100Mbps_hdx', '2.5Gbps_fdx']))
    switch_ecs2510fp_model.ports.append(Port(id='2', poe_type=Port.poe_bt_type, speed_cap=['auto', '1Gbps_fdx', '100Mbps_fdx', '100Mbps_hdx', '2.5Gbps_fdx']))
    switch_ecs2510fp_model.ports.append(Port(id='3', poe_type=Port.poe_bt_type, speed_cap=['auto', '1Gbps_fdx', '100Mbps_fdx', '100Mbps_hdx', '2.5Gbps_fdx']))
    switch_ecs2510fp_model.ports.append(Port(id='4', poe_type=Port.poe_bt_type, speed_cap=['auto', '1Gbps_fdx', '100Mbps_fdx', '100Mbps_hdx', '2.5Gbps_fdx']))
    switch_ecs2510fp_model.ports.append(Port(id='5', poe_type=Port.poe_bt_type, speed_cap=['auto', '1Gbps_fdx', '100Mbps_fdx', '100Mbps_hdx', '2.5Gbps_fdx']))
    switch_ecs2510fp_model.ports.append(Port(id='6', poe_type=Port.poe_bt_type, speed_cap=['auto', '1Gbps_fdx', '100Mbps_fdx', '100Mbps_hdx', '2.5Gbps_fdx']))
    switch_ecs2510fp_model.ports.append(Port(id='7', poe_type=Port.poe_bt_type, speed_cap=['auto', '1Gbps_fdx', '100Mbps_fdx', '100Mbps_hdx', '2.5Gbps_fdx']))
    switch_ecs2510fp_model.ports.append(Port(id='8', poe_type=Port.poe_bt_type, speed_cap=['auto', '1Gbps_fdx', '100Mbps_fdx', '100Mbps_hdx', '2.5Gbps_fdx']))
    switch_ecs2510fp_model.ports.append(Port(id='F1', speed_cap=['auto', '1Gbps_fdx', '10Gbps_fdx']))
    switch_ecs2510fp_model.ports.append(Port(id='F2', speed_cap=['auto', '1Gbps_fdx', '10Gbps_fdx']))

    try:
        Model.objects.insert([ap_ecw230_model, switch_ecs2510fp_model])
    except Exception as e:
        print(str(e))
        raise

if __name__ == '__main__':
    add_custom_models_to_collection()