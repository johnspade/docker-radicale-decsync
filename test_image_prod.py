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
                "--read-only",
                "--security-opt=no-new-privileges:true",
                "--pids-limit",
                "50",
                "--memory",
                "256M",
                "radicale-under-test",
            ]
        )
        .decode()
        .strip()
    )

    yield testinfra.get_host("docker://" + docker_id)

    # teardown
    subprocess.check_call(["docker", "rm", "-f", docker_id])


def test_process(host):
    output = host.check_output("cat /proc/*/cmdline 2>/dev/null | tr '\\0' ' '")
    assert "radicale" in output


def test_port(host):
    assert host.check_output("curl -s -o /dev/null -w '%{http_code}' --retry 5 --retry-connrefused http://localhost:5232") == "302"


def test_version(host):
    assert host.check_output("/venv/bin/radicale --version") == "3.7.7"


def test_user(host):
    user = "radicale"
    assert host.user(user).uid == 2999
    assert host.user(user).gid == 2999
    assert host.user(user).shell == "/bin/false"


def test_data_folder_writable(host):
    folder = "/data"
    assert host.file(folder).user == "radicale"
    assert host.file(folder).group == "radicale"
    assert host.file(folder).mode == 0o770
