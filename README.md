# Whirlpool's Sixth Sense (unofficial)

Unofficial API for Whirlpool's 6th Sense appliances.

As an example on how to use this library, please check the implementation of Home Assistant's [Whirlpool Integration](https://www.home-assistant.io/integrations/whirlpool), or take a look at the `whirlpool_ac.py` file.

If a command does not work, check if it works through the official app.

# NOTICE

Use this at your own risk. If, by using this software, any damage is caused to your appliance, or if you get too hot because your AC got crazy and now you can't sleep, the developers of this software or the manufacturer of your appliance cannot be blamed.

# ADDENDUM

This fork implements a poorly written bridge to a mqtt server. Actually it is configured to forward to a set of attributes from a Whirlpool Oven. Edit 'config.yaml' to meet your requirements.