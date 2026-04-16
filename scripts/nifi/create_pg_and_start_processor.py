import argparse
import sys
import uuid

import requests
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create a NiFi Process Group and start a processor using the NiFi REST/OpenAPI endpoints."
    )
    parser.add_argument(
        "--base-url",
        default="https://localhost:8443/nifi-api",
        help="NiFi API base URL",
    )
    parser.add_argument("--username", default="admin", help="NiFi username")
    parser.add_argument("--password", required=True, help="NiFi password")
    parser.add_argument(
        "--verify",
        default="false",
        help="TLS verification: true, false, or path to a CA bundle file",
    )
    parser.add_argument(
        "--pg-name",
        default="OpenAPI Demo PG",
        help="Name of the new Process Group",
    )
    parser.add_argument(
        "--processor-type",
        default="org.apache.nifi.processors.standard.GenerateFlowFile",
        help="Fully qualified processor type",
    )
    parser.add_argument(
        "--processor-name",
        default="GenerateFlowFile Demo",
        help="Name of the new processor",
    )
    parser.add_argument(
        "--pg-x", type=float, default=400.0, help="X position for the Process Group"
    )
    parser.add_argument(
        "--pg-y", type=float, default=200.0, help="Y position for the Process Group"
    )
    parser.add_argument(
        "--proc-x", type=float, default=80.0, help="X position for the processor"
    )
    parser.add_argument(
        "--proc-y", type=float, default=80.0, help="Y position for the processor"
    )
    parser.add_argument(
        "--scheduling-period",
        default="30 sec",
        help="Scheduling period for the processor",
    )
    return parser.parse_args()


def resolve_verify(value):
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return value


class NiFiClient:
    def __init__(self, base_url, username, password, verify):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.verify = verify
        self.session = requests.Session()
        self.session.verify = verify
        self.session.headers.update({"Accept": "application/json"})
        self.client_id = f"codex-{uuid.uuid4()}"

    def authenticate(self):
        response = self.session.post(
            f"{self.base_url}/access/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"username": self.username, "password": self.password},
            timeout=30,
        )
        response.raise_for_status()
        token = response.text.strip()
        self.session.headers["Authorization"] = f"Bearer {token}"
        return token

    def request_json(self, method, path, **kwargs):
        response = self.session.request(
            method,
            f"{self.base_url}{path}",
            timeout=30,
            **kwargs,
        )
        if not response.ok:
            print(f"[ERROR] {method} {path} failed: {response.status_code}", file=sys.stderr)
            print(response.text, file=sys.stderr)
            response.raise_for_status()
        if response.text:
            return response.json()
        return None

    def get_root_process_group_id(self):
        entity = self.request_json("GET", "/flow/process-groups/root")
        return entity["processGroupFlow"]["id"]

    def find_processor_type(self, processor_type):
        entity = self.request_json("GET", "/flow/processor-types")
        for item in entity["processorTypes"]:
            if item["type"] == processor_type:
                return item
        raise ValueError(f"Processor type not found: {processor_type}")

    def create_process_group(self, parent_group_id, name, x, y):
        payload = {
            "revision": {
                "clientId": self.client_id,
                "version": 0,
            },
            "component": {
                "name": name,
                "position": {
                    "x": x,
                    "y": y,
                },
            },
        }
        return self.request_json(
            "POST",
            f"/process-groups/{parent_group_id}/process-groups",
            json=payload,
        )

    def create_processor(
        self,
        process_group_id,
        processor_type,
        bundle,
        name,
        x,
        y,
        scheduling_period,
    ):
        payload = {
            "revision": {
                "clientId": self.client_id,
                "version": 0,
            },
            "component": {
                "name": name,
                "type": processor_type,
                "bundle": {
                    "group": bundle["group"],
                    "artifact": bundle["artifact"],
                    "version": bundle["version"],
                },
                "position": {
                    "x": x,
                    "y": y,
                },
                "config": {
                    "schedulingPeriod": scheduling_period,
                    "autoTerminatedRelationships": ["success"],
                },
            },
        }
        return self.request_json(
            "POST",
            f"/process-groups/{process_group_id}/processors",
            json=payload,
        )

    def start_processor(self, processor_id, revision):
        payload = {
            "revision": {
                "clientId": self.client_id,
                "version": revision["version"],
            },
            "state": "RUNNING",
        }
        return self.request_json(
            "PUT",
            f"/processors/{processor_id}/run-status",
            json=payload,
        )


def main():
    args = parse_args()
    client = NiFiClient(
        base_url=args.base_url,
        username=args.username,
        password=args.password,
        verify=resolve_verify(args.verify),
    )

    client.authenticate()
    root_group_id = client.get_root_process_group_id()
    processor_type = client.find_processor_type(args.processor_type)

    created_pg = client.create_process_group(
        parent_group_id=root_group_id,
        name=args.pg_name,
        x=args.pg_x,
        y=args.pg_y,
    )
    pg_id = created_pg["id"]

    created_processor = client.create_processor(
        process_group_id=pg_id,
        processor_type=processor_type["type"],
        bundle=processor_type["bundle"],
        name=args.processor_name,
        x=args.proc_x,
        y=args.proc_y,
        scheduling_period=args.scheduling_period,
    )
    processor_id = created_processor["id"]

    started_processor = client.start_processor(
        processor_id=processor_id,
        revision=created_processor["revision"],
    )

    print("Created Process Group:")
    print(f"  name: {created_pg['component']['name']}")
    print(f"  id:   {pg_id}")
    print("")
    print("Created and started Processor:")
    print(f"  name:   {started_processor['component']['name']}")
    print(f"  type:   {started_processor['component']['type']}")
    print(f"  id:     {processor_id}")
    print(f"  state:  {started_processor['component']['state']}")
    print(f"  bundle: {processor_type['bundle']['group']}:{processor_type['bundle']['artifact']}:{processor_type['bundle']['version']}")


if __name__ == "__main__":
    main()
