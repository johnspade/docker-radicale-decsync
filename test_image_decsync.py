import subprocess

import pytest
import testinfra


@pytest.fixture(scope="session")
def host():
    subprocess.check_call(["docker", "build", "-t", "radicale-under-test", "."])
    docker_id = (
        subprocess.check_output(["docker", "run", "-d", "--init", "radicale-under-test"])
        .decode()
        .strip()
    )

    yield testinfra.get_host("docker://" + docker_id)

    # teardown
    subprocess.check_call(["docker", "rm", "-f", docker_id])


VCALENDAR = "\r\n".join([
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Test//Test//EN",
    "BEGIN:VEVENT",
    "UID:test-decsync-event@test",
    "DTSTART:20250101T120000Z",
    "DTEND:20250101T130000Z",
    "SUMMARY:DecSync Test Event",
    "END:VEVENT",
    "END:VCALENDAR",
])


def test_decsync_storage(host):
    # Wait for Radicale to start
    host.check_output(
        "curl -s -o /dev/null --retry 5 --retry-connrefused http://localhost:5232"
    )

    # Create user principal, then calendar
    host.check_output("curl -s -X MKCOL http://localhost:5232/user/")
    host.check_output("curl -s -X MKCALENDAR http://localhost:5232/user/test-calendar/")

    # DecSync remaps "test-calendar" to "calendars-test-calendar" on disk
    put_cmd = (
        "curl -s -f -X PUT "
        "-H 'Content-Type: text/calendar' "
        "--data-binary @- "
        "http://localhost:5232/user/calendars-test-calendar/test-event.ics"
    )
    host.check_output(f"echo '{VCALENDAR}' | {put_cmd}")

    # Verify event stored in filesystem
    assert host.file(
        "/data/collections/collection-root/user/calendars-test-calendar/test-event.ics"
    ).exists

    # Verify DecSync directory was populated with sync data
    decsync_files = host.check_output("find /data/decsync -type f")
    assert decsync_files, "DecSync directory should contain sync files"
    assert "calendars/test-calendar" in decsync_files
