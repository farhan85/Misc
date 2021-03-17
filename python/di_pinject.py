#!/usr/bin/env python3

import boto3
import pinject


class ClassOne(object):
   def __init__(self, username, stack):
       self.prop = '{}:{}'.format(stack, username)


class ClassTwo(object):
    def __init__(self, class_one, level, sqs_client):
        self.prop = '{}:{}'.format(class_one.prop, level)
        self.sqs = sqs_client

    def __str__(self):
        return self.prop


class AwsClientBindingSpec(pinject.BindingSpec):
    def provide_boto_session(self, region):
        return boto3.Session(region_name=region)

    def provide_sqs_client(self, boto_session):
        return boto_session.resource('sqs')


class ConfigBindingSpec(pinject.BindingSpec):
    def __init__(self, stage, region):
        super().__init__()
        self.stage = stage
        self.region = region

    def configure(self, bind):
        bind('username', to_instance='foobar1234')
        bind('level', to_instance=42)
        bind('stage', to_instance=self.stage)
        bind('region', to_instance=self.region)
        bind('stack', to_instance='{}-{}'.format(self.stage, self.region))


obj_graph = pinject.new_object_graph(binding_specs=[
    ConfigBindingSpec('prod', 'us-east-1'),
    AwsClientBindingSpec()])

class_two = obj_graph.provide(ClassTwo)
print(str(class_two.prop))
print([q for q in class_two.sqs.queues.all()])
