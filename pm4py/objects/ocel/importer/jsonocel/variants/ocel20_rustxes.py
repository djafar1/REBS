'''
    This file is part of PM4Py (More Info: https://pm4py.fit.fraunhofer.de).

    PM4Py is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    PM4Py is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with PM4Py.  If not, see <https://www.gnu.org/licenses/>.
'''
from typing import Optional, Dict, Any
from pm4py.objects.ocel.obj import OCEL


def apply(file_path: str, parameters: Optional[Dict[Any, Any]] = None) -> OCEL:
    """
    Imports an OCEL 2.0 JSON using the RUSTXES parser.

    Parameters
    ---------------
    file_path
        Path to the OCEL 2.0 JSON
    parameters
        Optional parameters.

    Returns
    ---------------
    ocel
        Object-centric event log
    """
    if parameters is None:
        parameters = {}

    import rustxes

<<<<<<<< HEAD:pm4py/algo/querying/llm/connectors/openai.py
    import openai

    client = openai.OpenAI(api_key=api_key)

    message = {"role": "user", "content": query}

    response = client.chat.completions.create(model=model, messages=[message])

    return response.choices[0].message.content
========
    return rustxes.import_ocel_json_pm4py(file_path)
>>>>>>>> origin/feature/dcr_in_pm4py_revised:pm4py/objects/ocel/importer/jsonocel/variants/ocel20_rustxes.py
