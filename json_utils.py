# v1 100% funcional

import json

class JSONutils:
    def cam_to_json(self, 
                    input: str = 'cam_params.txt', 
                    output: str = 'cam_params.json', 
                    export: bool = False) -> dict:
        '''
        Convert the standard cam params from Daheng format to json

        Args:
        input: str containing the path to .txt params file
        output: str containing the path to .json params file

        Return:
        None
        '''
        params = {}
        balance_ratio_color: str = None # name of last balance ratio read

        with open(input, 'r') as file:
            for _ in file:
                line = _.split(sep=None) # None as any whitespace
                try: 
                    if balance_ratio_color != None: # Condition to parse different tags with the same name from the original document
                        # BalanceRatio -> BalanceRatioRed, BalanceRatioGreen and BalanceRatioBlue
                        params[line[0]+balance_ratio_color] = float(line[1])
                        balance_ratio_color = None
                    else: params[line[0]] = float(line[1]) # If the tag isn't associated with a color, just parse the float value
                except: 
                    # particular case for BalanceRatioSelector for independent entries based on ENUM color feature
                    if line[0] == 'BalanceRatioSelector':
                        balance_ratio_color = str(line[1])
                        params[str(line[0])+str(line[1])] = line[1]
                    else: params[line[0]] = str(line[1])

        if export:
            with open(output, 'w') as file:
                json.dump(params, file, indent=4)

        return params

    def json_to_cam(self, input: str = 'cam_params.json', output: str = 'cam_paramy.txt', export: bool = False) -> dict:
        '''
        Convert the standard cam params from json to Daheng format (saved as the name in 'output' arg)

        Args:
        input: str containing the path to .json params file
        output: str containing the path to .txt params file
        export: bool to save, or not, the parsed info to .txt

        Return:
        Dict containing parsed data
        '''
        with open(input, 'r') as file:
            data = json.load(file)

        params = {}

        if isinstance(data, dict):
            for key, value in data.items():
                # particular case for BalanceRatioSelector for independent entries based on ENUM feature
                if 'BalanceRatioSelector' in key: params['BalanceRatioSelector'] = value
                else: params[key] = value
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    for key, value in item.items():
                        # particular case for BalanceRatioSelector for independent entries based on ENUM feature
                        if 'BalanceRatioSelector' in key: params['BalanceRatioSelector'] = value
                        else: params[key] = value

        if export:
            with open(output, 'w') as file:
                for key, value in params.items():
                    file.write(f'{key} {value}\n') 

        return params


    def dict_to_cam(self, input: dict, output: str = 'cam_paramy.txt', export: bool = False) -> dict:
        '''
        Convert the standard cam params from dict to Daheng format (saved as the name in 'output' arg)

        Args:
        input: dict containing cam params
        output: str containing the path to .txt params file
        export: bool to save, or not, the parsed info to .txt

        Return:
        Dict containing parsed data
        '''
        params = {}

        for key, value in input.items():
            # particular case for BalanceRatioSelector for independent entries based on ENUM feature
            if 'BalanceRatioSelector' in key: params['BalanceRatioSelector'] = value
            else: params[key] = value

        if export:
            with open(output, 'w') as file:
                for key, value in params.items():
                    file.write(f'{key} {value}\n') 

        return params


if __name__ == '__main__':
    utils = JSONutils()
    print(utils.json_to_cam(export=True))