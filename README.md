# BlueOS-Cygnus-UT

BlueOS-Cygnus-UT is a BlueOS Extension for the Cygnus Mini ROV Mountable Ultrasonic Thickness Gauge

## Changelog

### v0.0.1
 - Initial development release

## User Installation

Install it from [BlueOS extensions tab](https://blueos.cloud/docs/software/onboard/BlueOS-1.1/extensions/).

The service will show in the "Extension Manager" section in BlueOS, where there are some configuration options.

## Developer Info

To build:

Enable qemu static support with a docker:

```
docker buildx create --name multiarch --driver docker-container --use
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

Then build it:

`docker buildx build --platform linux/amd64,linux/arm/v7 . -t YOURDOCKERHUBUSER/YOURDOCKERHUBREPO:latest --output type=registry
`
