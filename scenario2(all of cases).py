import subprocess
import time
import datetime
import boto3

from tqdm import tqdm

import ssh_scripts.playbook as playbook

ec2_client = boto3.client('ec2', region_name='us-west-2')
ec2_resource = boto3.resource('ec2', region_name='us-west-2')

GROUP_NUMBER = 4
CREATE_GRPUP = [i for i in range(GROUP_NUMBER)]

start_time = datetime.datetime.now()
# create infrastructure by group
with open(f'terraform.log', 'w') as f:  # Created separately for reuse of some resources, such as VPCs
    subprocess.run(['terraform', 'apply', '-auto-approve', '-target', 'module.read-instances', '-var',
                   f'group={CREATE_GRPUP}'], cwd='infrastructure/Scenario2', stdout=f, stderr=f, encoding='utf-8')
    subprocess.run(['terraform', 'apply', '-auto-approve', '-var', f'group={CREATE_GRPUP}'],
                   cwd='infrastructure/Scenario2', stdout=f, stderr=f, encoding='utf-8')

print('\nComplete infrastructure creation')

# checking instance status
while True:
    print('checking instance status...')
    instances = ec2_client.describe_instances(Filters=[
        {
            'Name': 'tag:Name',
            'Values': ['migration-test_*']
        }
    ])

    all_running = True

    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_obj = ec2_resource.Instance(instance_id)

            instance_state = instance_obj.state['Name']

            if instance_state == 'terminated':
                print(f"Instance {instance_id} is terminated")
                break

            status = ec2_client.describe_instance_status(
                InstanceIds=[instance_id])
            if 'InstanceStatuses' not in status or status['InstanceStatuses'][0]['InstanceStatus']['Status'] != 'ok':
                print(
                    f"Instance {instance_id} is not yet ready. Waiting 5 seconds...")
                all_running = False
                break

        if not all_running:
            break

    if all_running:
        print('All instances are running')
        break
    time.sleep(10)

print('Pass all instance health checks')

subprocess.run('rm -f ansible.log', shell=True)

# Execute an Ansible command to start the migration test.
# for i in range(GROUP_NUMBER):
#     dst = [i for i in range(GROUP_NUMBER)]
#     dst.remove(i)
#     playbook.scenario2(i, dst)
for i in tqdm(range(GROUP_NUMBER), desc='Processing'):
    dst = [j for j in range(GROUP_NUMBER) if j != i]
    playbook.scenario2(i, dst)
    
# destroy infrastructure by group
with open(f'terraform.log', 'a') as f:
    p = subprocess.Popen(['terraform', 'destroy', '-auto-approve', '-var',
                         f'group={CREATE_GRPUP}'], cwd='infrastructure/Scenario2', stdout=f, stderr=f)
    p.wait()

end_time = datetime.datetime.now()

elapsed_time = end_time - start_time
total_seconds = elapsed_time.total_seconds()
print(f'total time : {total_seconds}')