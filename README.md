# LeagueStartAuditor

Get historical information on a build's price early in the league to determine whether or not it would be a good league starter.

## Usage

Tested using Podman, replace `podman` with `docker` if using Docker.

1. `git clone git@github.com:will-a/LeagueStartAuditor.git && cd LeagueStartAuditor`

2. `podman build -t lsa .`

3. `podman run -p 4444:4444 lsa`

4. Open browser and go to http://localhost:4444
