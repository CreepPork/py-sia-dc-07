# py-sia-dc-07

A simple Python script that listens on a given TCP ip/port and awaits messages from a SIA DC-07 protocol supported device.

The script will handle all device communication with the supported device.

After parsing the contents of the TCP message then it will relay the JSON-formatted message to a web server endpoint of your choice. There, you can act upon the contents of the message itself.

## Payload

```json
{
  "username": "",
  "password": "",
  "asd_id": "1002",
  "event_qualifier": "3",
  "event_code": "602",
  "group_number": "000",
  "device_or_sensor_number": "01"
}
```

## Installation

You can install the package via Git and the dependencies via pip. You'll need to configure the `.env` file too:

```bash
git clone https://github.com/CreepPork/py-sia-dc-07
pip install -r ./requirements.txt
cp .env.example .env
```

## Usage

```bash
python3 app.py
```

### Security

If you discover any security related issues, please email security@garkaklis.com instead of using the issue tracker.

## Credits

- [Ralfs Garkaklis](https://github.com/CreepPork)
- [All Contributors](https://github.com/CreepPork/py-sia-dc-07/contributors)

## License

The MIT License (MIT). Please see [License File](LICENSE.md) for more information.
