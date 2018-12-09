# RF-Xfil | Prototype Toolkit for Data Exfiltration over Radio Frequencies
## Started by Jie Feng, Ragul & Andre Dec 2018 @ HackSmith v2.0 

![HackSmith v2 Award](hacksmithv2/HackSmith_Award.jpg)

Imagine your dongle (of which many modern devices depend on) is exfiltrating information over RF! Thats exactly the Proof-Of-Concept we managed to showcase at HackSmith v2 over the 8-9 Dec 2018 weekend.

By writing "simulated malicious" code masquerading as the device driver for a inexpensive off the shelf USB-to-VGA dongle based off the infamous Fresco Logic FL2000 chipset, we were able to exfiltrate not only the audio from the victim laptop's microphone and SSTV of a screenshot, but also built modulation (inspired by fax and work done by romanz/amodem) robust enough to transfer screenshots and any arbitary files.

Demodulation code to be used with generic inexpensive RTL-SDRs is also in here.

We feel that more people should take an active interest in & do research into electronics & RF.

Lets see what other overpowered embedded devices can be used to do mindblowing things.
