from charms import layer
from charms.reactive import hook, clear_flag, set_flag, when, when_any
from charms.reactive import when_not


@hook('upgrade-charm')
def upgrade_charm():
    clear_flag('charm.started')


@when('charm.started')
def charm_ready():
    layer.status.active('')


@when_any('layer.docker-resource.oci-image.changed', 'config.changed')
def update_image():
    clear_flag('charm.started')


@when('layer.docker-resource.oci-image.available')
@when_not('charm.started')
def start_charm():
    layer.status.maintenance('configuring container')

    image_info = layer.docker_resource.get_info('oci-image')

    layer.caas_base.pod_spec_set(
        spec={
            'version': 2,
            'serviceAccount': {
                'global': True,
                'rules': [
                    {
                        'apiGroups': [''],
                        'resources': ['configmaps', 'secrets', 'nodes',
                                      'pods', 'services', 'resourcequotas',
                                      'replicationcontrollers', 'limitranges',
                                      'persistentvolumeclaims',
                                      'persistentvolumes', 'namespaces',
                                      'endpoints'],
                        'verbs': ['list', 'watch'],
                    },
                    {
                        'apiGroups': ['extensions'],
                        'resources': ['daemonsets', 'deployments',
                                      'replicasets', 'ingresses'],
                        'verbs': ['list', 'watch'],
                    },
                    {
                        'apiGroups': ['apps'],
                        'resources': ['daemonsets', 'deployments',
                                      'replicasets', 'statefulsets'],
                        'verbs': ['list', 'watch'],
                    },
                    {
                        'apiGroups': ['batch'],
                        'resources': ['cronjobs', 'jobs'],
                        'verbs': ['list', 'watch'],
                    },
                    {
                        'apiGroups': ['autoscaling'],
                        'resources': ['horizontalpodautoscalers'],
                        'verbs': ['list', 'watch'],
                    },
                    {
                        'apiGroups': ['policy'],
                        'resources': ['poddisruptionbudgets'],
                        'verbs': ['list', 'watch'],
                    },
                    {
                        'apiGroups': ['certificates.k8s.io'],
                        'resources': ['certificatesigningrequests'],
                        'verbs': ['list', 'watch'],
                    },
                    {
                        'apiGroups': ['storage.k8s.io'],
                        'resources': ['storageclasses'],
                        'verbs': ['list', 'watch'],
                    },
                    {
                        'apiGroups': ['autoscaling.k8s.io'],
                        'resources': ['verticalpodautoscalers'],
                        'verbs': ['list', 'watch'],
                    },
                ],
            },
            'containers': [
                {
                    'name': 'kube-state-metrics',
                    'imageDetails': {
                        'imagePath': image_info.registry_path,
                        'username': image_info.username,
                        'password': image_info.password,
                    },
                    'ports': [{
                        'name': 'http-metrics',
                        'containerPort': 8080
                        }, {
                        'name': 'telemetry',
                        'containerPort': 8081
                        }
                    ],
                    'livenessProbe': {
                        'initialDelaySeconds': 5,
                        'timeoutSeconds': 5,
                        'httpGet': {
                            'path': '/healthz',
                            'port': 8080
                        }
                    },
                    'readinessProbe': {
                        'initialDelaySeconds': 5,
                        'timeoutSeconds': 5,
                        'httpGet': {
                            'path': '/',
                            'port': 8080
                        }
                    },
                }
            ],
        },
    )

    layer.status.maintenance('creating container')
    set_flag('charm.started')
