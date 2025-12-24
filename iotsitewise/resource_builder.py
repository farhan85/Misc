# Helper classes for building AWS IoT SiteWise/Events resources
# Examples of how to use these classes are at the end of this file

class AssetModelBuilder:
    def __init__(self, name):
        self.name = name
        self.description = None
        self.hierarchies = []
        self.properties = []
        self.composite_models = []

    def set_description(self, description):
        self.description = description

    def add_attribute(self, name, data_type, default_value=None, unit=None):
        self.properties.append(self._build_attribute(name, data_type, default_value, unit))

    def add_measurement(self, name, data_type, unit=None):
        self.properties.append(self._build_measurement(name, data_type, unit))

    def add_transform(self, name, data_type, equation, variable_map, unit=None):
        self.properties.append(self._build_transform(name, data_type, equation, variable_map, unit=None))

    def add_metric(self, name, data_type, tumbling_window, equation, variable_map, unit=None):
        self.properties.append(self._build_metric(name, data_type, tumbling_window, equation, variable_map, unit))

    def add_hierarchy(self, name, child_model_id):
        self.hierarchies.append({'name': name, 'childAssetModelId': child_model_id})

    def add_iotevents_alarm(self, name, alarm_model_arn=None):
        composite_model = {
            'name': name,
            'type': 'AWS/ALARM',
            'properties': [
                self._build_attribute('AWS/ALARM_TYPE', 'STRING', 'IOT_EVENTS'),
                self._build_struct_measurement('AWS/ALARM_STATE', 'AWS/ALARM_STATE'),
            ]
        }
        if alarm_model_arn:
            composite_model['properties'].append(self._build_attribute('AWS/ALARM_SOURCE', 'STRING', alarm_model_arn))
        self.composite_models.append(composite_model)

    @classmethod
    def _build_attribute(cls, name, data_type, default_value=None, unit=None):
        prop = {
            'name': name,
            'dataType': data_type,
            'type': { 'attribute': {} }
        }
        if default_value:
            prop['type']['attribute']['defaultValue'] = default_value
        if unit:
            prop['unit'] = unit
        return prop

    @classmethod
    def _build_measurement(cls, name, data_type, unit=None):
        prop = {
            'name': name,
            'dataType': data_type,
            'type': { 'measurement': {} }
        }
        if unit:
            prop['unit'] = unit
        return prop

    @classmethod
    def _build_struct_measurement(cls, name, data_type_spec, unit=None):
        prop = {
            'name': name,
            'dataType': 'STRUCT',
            'dataTypeSpec': data_type_spec,
            'type': { 'measurement': {} }
        }
        if unit:
            prop['unit'] = unit
        return prop

    @classmethod
    def _build_transform(cls, name, data_type, equation, variable_map, unit=None):
        prop = {
            'name': name,
            'dataType': data_type,
            'type': {
                'transform': {
                    'expression': equation,
                    'variables': []
                }
            }
        }
        if not isinstance(variable_map, list):
            variable_map = [variable_map]
        for variable in variable_map:
            prop_name, prop_id = variable.split('=')
            prop['type']['transform']['variables'].append({
                'name': prop_name,
                'value': { 'propertyId': prop_id }
            })
        if unit:
            prop['unit'] = unit
        return prop

    @classmethod
    def _build_metric(cls, name, data_type, tumbling_window, equation, variable_map, unit=None):
        prop = {
            'name': name,
            'dataType': data_type,
            'type': {
                'metric': {
                    'expression': equation,
                    'variables': [],
                    'window': {
                        'tumbling': {
                            'interval': tumbling_window
                        }
                    }
                }
            }
        }
        if not isinstance(variable_map, list):
            variable_map = [variable_map]
        for variable in variable_map:
            prop_name, prop_id = variable.split('=')
            if '|' in prop_id:
                hierarchy_id, prop_id = prop_id.split('|')
                value = {'propertyId': prop_id, 'hierarchyId': hierarchy_id}
            else:
                value = {'propertyId': prop_id}
            prop['type']['metric']['variables'].append({'name': prop_name, 'value': value})
        if unit:
            prop['unit'] = unit
        return prop

    def build(self):
        model = {
            'assetModelName': self.name
        }
        if self.description:
            model['assetModelDescription'] = self.description
        if self.properties:
            model['assetModelProperties'] = self.properties
        if self.hierarchies:
            model['assetModelHierarchies'] = self.hierarchies
        if self.composite_models:
            model['assetModelCompositeModels'] = self.composite_models
        return model


class AlarmModelBuilder:
    def __init__(self, name):
        self.name = name
        self.role_arn = None
        self.severity = None
        self.alarm_rule = None
        self.alarm_capabilities = {}
        self.alarm_event_actions = None

    def set_description(self, description):
        self.description = description

    def set_role_arn(self, role_arn):
        self.role_arn = role_arn

    def set_severity(self, severity):
        self.severity = severity

    @classmethod
    def operator(cls, comparison_symbol):
        operator = {
            '>':  'GREATER',
            '>=': 'GREATER_OR_EQUAL',
            '<':  'LESS',
            '<=': 'LESS_OR_EQUAL',
            '=':  'EQUAL',
            '==': 'EQUAL',
            '!=': 'NOT_EQUAL',
            '<>': 'NOT_EQUAL'
        }
        return operator.get(comparison_symbol, comparison_symbol)

    def set_sitewise_rule(self, asset_model_id, monitored_prop_id, comparison, threshold_prop_id, alarm_state_prop_id):
        self.alarm_rule = {
            'simpleRule': {
                'inputProperty': f'$sitewise.assetModel.`{asset_model_id}`.`{monitored_prop_id}`.propertyValue.value',
                'comparisonOperator': self.operator(comparison),
                'threshold': f'$sitewise.assetModel.`{asset_model_id}`.`{threshold_prop_id}`.propertyValue.value'
            }
        }
        self.alarm_event_actions = {
            'alarmActions': [
                {
                    'iotSiteWise': {
                        'assetId': f'$sitewise.assetModel.`{asset_model_id}`.`{monitored_prop_id}`.assetId',
                        'propertyId': f"'{alarm_state_prop_id}'"
                    }
                }
            ]
        }

    def disable_on_initialization(self, disable):
        self.alarm_capabilities['initializationConfiguration'] = {'disabledOnInitialization': False}

    def acklowledge_flow(self, enable):
        self.alarm_capabilities['acknowledgeFlow'] = {'enabled': False}

    def build(self):
        model = {
            'alarmModelName': self.name,
            'roleArn': self.role_arn,
            'alarmRule': self.alarm_rule
        }
        if self.description:
            model['alarmModelDescription'] = self.description
        if self.severity:
            model['severity'] = self.severity
        if self.alarm_capabilities:
            model['alarmCapabilities'] = self.alarm_capabilities
        if self.alarm_event_actions:
            model['alarmEventActions'] = self.alarm_event_actions
        return model


if __name__ == '__main__':
    model_builder = AssetModelBuilder('TestAssetModelWithAlarm')
    model_builder.set_description('Example of an AssetModel with an Alarm')
    model_builder.add_attribute('temperature_threshold', 'DOUBLE', '50', 'celsius')
    model_builder.add_measurement('temperature_f', 'DOUBLE', 'fahrenheit')
    model_builder.add_transform('temperature_c', 'DOUBLE', '(32 * f - 32) * (5.0/9.0)', 'f=temperature_f')
    model_builder.add_metric('temperature_avg', 'DOUBLE', '5m', 'avg(t)', 't=temperature_c')
    model_builder.add_metric('rollup_metric', 'DOUBLE', '5m', 'sum(avg(x,y),earliest(z))',
         ['x=hierarchy_1|11111111-1111-1111-1111-111111111111',
          'y=hierarchy_1|22222222-2222-2222-2222-222222222222',
          'z=hierarchy_2|33333333-3333-3333-3333-333333333333'])
    model_builder.add_hierarchy('hierarchy_1', '44444444-4444-4444-4444-444444444444')
    model_builder.add_hierarchy('hierarchy_2', '55555555-5555-5555-5555-555555555555')
    model_builder.add_iotevents_alarm('temperature-alarm', 'arn:aws:iotevents:us-west-2:123456789012:alarmModel/TestAlarmModel')

    alarm_builder = AlarmModelBuilder('TestAlarmModel')
    alarm_builder.set_description('Example of a SiteWise-monitored Alarm')
    alarm_builder.set_role_arn('arn:aws:iam::123456789012:role/IoTEventsAlarmModelRole')
    alarm_builder.set_severity(5)
    alarm_builder.set_sitewise_rule(
        '66666666-6666-6666-6666-666666666666',
        '77777777-7777-7777-7777-777777777777',
        '>',
        '88888888-8888-8888-8888-888888888888',
        '99999999-9999-9999-9999-999999999999')
    alarm_builder.disable_on_initialization(False)
    alarm_builder.acklowledge_flow(True)

    import json
    print(json.dumps(model_builder.build(), indent=2))
    print(json.dumps(alarm_builder.build(), indent=2))

