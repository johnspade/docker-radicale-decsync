import configparser
import subprocess

import pytest
import testinfra


@pytest.fixture(scope="session")
def host():
    subprocess.check_call(["docker", "build", "-t", "radicale-under-test", "."])
    docker_id = (
        subprocess.check_output(
            [
                "docker",
                "run",
                "-d",
                "--init",
                "-e",
                "RADICALE_CONFIG_WEB_TYPE=none",
                "-e",
                "RADICALE_CONFIG_AUTH_DELAY=5",
                "radicale-under-test",
            ]
        )
        .decode()
        .strip()
    )

    yield testinfra.get_host("docker://" + docker_id)

    # teardown
    subprocess.check_call(["docker", "rm", "-f", docker_id])


def test_config(host):
    config_content = host.check_output("cat /config/config")

    parser = configparser.ConfigParser()
    parser.read_string(config_content)

    assert parser.get("web", "type") == "none"
    assert parser.get("auth", "delay") == "5"
