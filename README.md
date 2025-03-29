# very_abstract_network_PDU_journey_simulator

A visual interactive tool that -abstractly- mimics packet/frame traversal dynamics as per fundamental computer networking concepts. The main goal is to enable the user to observe a complete, abstract end-to-end communication cycle and see the PDUs (like frames and packets) that are part of this complete cycle of a request and its corresponding response between two hosts.

I wrote this program to demostrate/apply to what I've learned from studying this [Networking Fundamentals Video Series](https://www.youtube.com/playlist?list=PLIFyRwBY_4bRLmKfP1KnZA6rZbRHtxmXi), alongside with this [Subnetting Video Series](https://www.youtube.com/playlist?list=PLIFyRwBY_4bQUE4IB5c4VPRyDoLgOdExE) from the same Instructor. The main series teaches how network communication occurs and how data flows between different network entities in any network as per the the OSI model.

I'm learning this as part of my plan to study web app development, specifically, backend development. I will most likely zoom-in a bit after this and study and learn about common networking protocols of today's internet.

The OSI model is a very good **conceptual** model or framework to **understand**, **describe**, and **communicate** how different components of a network interact with each other. It being a conceptual model/framework means it's more of a **theoritical** model and less of a practical model for implementation of networks (like a physician explaining how a typical car works without bothering how it's manufactued). The OSI model being conceptual and theoritical, doesn't mean it's a 'skimmed' model, but instead, it means it serves a close-but-different purpose compared to other more practical models, in fact, one of the reasons the OSI model is less practical to implement is it's overly comprehensive/broad. *Another reason is that the OSI model was developed before specific protocols were widely established, leading to a theoretical framework that lacks direct compatibility with many established real-world protocols used on the internet.*

### What the hell is a PDU?

It simply means any generic **package of information**/**unit of data** passing around in a network. For example, a network **packet** is a PDU, same goes for a network **frame** or a **segment**, we can even call **program data** that do not have network headers yet, a PDU. It's a pretty inclusive term, isnt it? That is the reason I've chosen to use it, it's perfectly descriptive of any generic data unit being transmitted, regardless of which layer/s headers does it hold.
Yes, I could've just used ``packet/frame`` instead of ``PDU``, sticking to more common network terms most of us already know, but "PDU" is more inclusive and more accurate refering to data at any of the layers, and lastly, it is shorter than "packet/frame".

**The following are some formal definitions of a PDU:**
*(Doesn't mean any other less formal definition is necessarily wrong/bad, since we can make endless non-wrong definitions of these things anyway, but formal definitions are really good and non confusing)*

* According to The Internet Engineering Task Force, in [RFC 1208](https://datatracker.ietf.org/doc/html/rfc1208):
  
  > PDU: Protocol Data Unit.  This is OSI terminology for "packet."
  > A PDU is a data object exchanged by protocol machines (entities) within a given layer. PDUs consist of both Protocol Control Information (PCI) and user data.

* According to [Lenovo.com](https://www.lenovo.com/us/en/glossary/what-is-pdu/) *(I don't like to cite companies on non-proprietery/open information but it won't hurt this time)*:
  
  > PDU stands for Protocol Data Unit. It's a term used in networking and telecommunications to refer to the data unit that's transmitted between network entities. Essentially, it's the package of information that gets passed around in a network.
  > 
  > ...
  > 
  > How does a PDU differ from a frame or a packet?
  > 
  > A PDU is a generic term that can refer to data units at various layers of the OSI model. A frame is a PDU at the Data Link Layer, while a packet is a PDU at the Network Layer. Each term specifies the layer at which the data unit operates.

* According to the European Telecommunications Standards Institute, in [ETS 300 217-1](https://www.etsi.org/deliver/etsi_i_ets/300200_300299/30021701/01_60/ets_30021701e01p.pdf) (page 10):
  
  > Protocol Data Unit (PDU): is a block of data which consists of all information (user data, addressing information and service parameters) related to a single, self-contained service instance.
  > 
  > NOTE 2: This definition covers the basic connectionless service PDU.
  > 
  > NOTE 3: Other terms used for the same purpose are: frame, message, datagram.

* According to [the wiki](https://wiki.wireshark.org/PDU) for the Wireshark open network protocol analyzer *(although not formal)*:
  
  > PDU is short for "Protocol Data Unit". This basically means an amount of information delivered through a network layer.
  > 
  > Colloquial term is "packet" 😃 But that is not the same as PDUs from higher network layers may contain more data than a PDU from a lower layer may carry. In this case, the higher layer PDU is split into several PDUs from the lower layer. Furthermore, a PDU from a lower layer might contain multiple PDUs from higher network layers.

I know, that looks like a very unnecessary load of definitions elaborating on a minor README term, but providing extra clarity is not a harm in my case, especially given that I enjoy this kind of writing (besides the fact I personally like to provide extra clarity and that I want all the definitions in one place for myself).
