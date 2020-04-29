# py-sia-dc-07

A simple Python script that listens on a given TCP ip/port and awaits messages from a SIA DC-07 protocol supported device.

The script will handle all device communication with the supported device.

After parsing the contents of the TCP message then it will relay the JSON-formatted message to a web server endpoint of your choice. There, you can act upon the contents of the message itself.

Currently only ADC-CID (Adamco Contact ID) messages are supported.

## Payload

Example payload:

```py
b'\n9EC40027"ADC-CID"0001L0#1002[#1002|1602 00 001]\r'
```

Example result:

```json
{
  "sequence_number": 1,
  "reciever_number": -1,
  "line_number": 0,
  "account_number": 1002,
  "event_qualifier": 1,
  "event_code": 602,
  "group_or_partion_number": "00",
  "zone_number_or_user_number": "001"
}
```

_Note:_ If the line or reciever number is not provided, it will be set to `-1`.

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
