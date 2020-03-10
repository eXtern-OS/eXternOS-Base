# Description

A PulseAudio client written in pure JavaScript for [node.js](http://nodejs.org/).

Currently most commands are implemented. SHM/MemFD-related commands are not supported.

# Table of Contents

* [Requirements](#requirements)
* [Installation](#installation)
* [Examples](#examples)
  * [Subscribe to all server events](#subscribe-to-all-server-events)
* [API](#api)
  * [Client](#client)
      * [Client events](#client-events)
      * [Client methods](#client-methods)

## Requirements

* [node.js](http://nodejs.org/) -- v6.0.0 or newer

## Installation

    npm install paclient

## Examples

### Subscribe to all server events

```js
const PAClient = require('paclient');

const pa = new PAClient();
pa.on('ready', () => {
  console.log('Ready');
  pa.subscribe('all');
}).on('close', () => {
  console.log('Connection closed');
}).on('new', (type, index) => {
  pa[getFnFromType(type)](index, (err, info) => {
    if (err) {
      console.log(`Could not fetch ${type}, index ${index}: ${err.message}`);
      return;
    }
    var name = info.name || info.description || '<unknown>';
    console.log(`"${name}" (${type}) added`);
  });
}).on('change', (type, index) => {
  pa[getFnFromType(type)](index, (err, info) => {
    if (err) {
      console.log(`Could not fetch ${type}, index ${index}: ${err.message}`);
      return;
    }
    var name = info.name || info.description || '<unknown>';
    console.log(`"${name}" (${type}) changed`);
  });
}).on('remove', (type, index) => {
  console.log(`Removed ${type}, index #${index}`);
});

pa.connect();

function getFnFromType(type) {
  var fn;
  switch (type) {
    case 'sink':
    case 'card':
    case 'source': fn = type; break;
    case 'sinkInput':
    case 'sourceOutput':
    case 'client':
    case 'module': fn = `${type}ByIndex`; break;
    default:
      throw new Error('Unexpected type: ' + type);
  }
  return 'get' + fn[0].toUpperCase() + fn.slice(1);
}
```

## API

### Client

#### Client events

* **ready**() - A successful, authenticated connection has been made.

* **close**() - The connection to the server has been closed.

* **new**(< _string_ >type, < _integer_ >index) - A new entity has been added.

* **change**(< _string_ >type, < _integer_ >index) - An existing entity has changed.

* **remove**(< _string_ >type, < _integer_ >index) - An existing entity has been removed.

#### Client methods

* **(constructor)**() - Creates and returns a new Client instance.

* **connect**([< _object_ >config]) - _(void)_ - Attempts a connection to a server using the information given in `config`. If no `path` or `host` are supplied then connection details are autodetected using the same algorithm as the official PulseAudio client library. Valid `config` options are:

    * **path** - _string_ - Path to a UNIX socket of the server. **Default:** Autodetected

    * **host** - _string_ - Hostname or IP address of the server. **Default:** Autodetected

    * **port** - _integer_ - Port number of the server. **Default:** `4713`

    * **cookie** - _mixed_ - An explicit cookie value to use when authenticating with the server. This can either be a _Buffer_ or a hex string of the appropriate length. **Default:** Autodetected

    * **properties** - _object_ - A set of properties to associate with the client on the server. These can be seen by other clients. **Default:** `{ application: { name: 'paclient.js' } }`

* **end**() - _(void)_ - If connected, this will close the connection to the server.

* **getModules**(< _function_ >callback) - _(void)_ - Retrieves a list of loaded modules. `callback` has 2 parameters: < _Error_ >err, < _array_ >modules.

* **getClients**(< _function_ >callback) - _(void)_ - Retrieves a list of connected clients. `callback` has 2 parameters: < _Error_ >err, < _array_ >clients.

* **getSinks**(< _function_ >callback) - _(void)_ - Retrieves a list of available sinks (outputs). `callback` has 2 parameters: < _Error_ >err, < _array_ >sinks.

* **getSources**(< _function_ >callback) - _(void)_ - Retrieves a list of available sources (inputs). `callback` has 2 parameters: < _Error_ >err, < _array_ >sources.

* **getSinkInputs**(< _function_ >callback) - _(void)_ - Retrieves a list of available sink inputs (streams connected to outputs). `callback` has 2 parameters: < _Error_ >err, < _array_ >sinkInputs.

* **getSourceOutputs**(< _function_ >callback) - _(void)_ - Retrieves a list of available source outputs (streams connected to inputs). `callback` has 2 parameters: < _Error_ >err, < _array_ >sourceOutputs.

* **getCards**(< _function_ >callback) - _(void)_ - Retrieves a list of available cards (hardware devices that usually combine a single source (for recording) and a single sink (for playback)). `callback` has 2 parameters: < _Error_ >err, < _array_ >cards.

* **getServerInfo**(< _function_ >callback) - _(void)_ - Retrieves information about the server. `callback` has 2 parameters: < _Error_ >err, < _object_ >info.

* **getModuleByIndex**(< _integer_ >index, < _function_ >callback) - _(void)_ - Retrieves a module by its index. `callback` has 2 parameters: < _Error_ >err, < _object_ >module.

* **getClientByIndex**(< _integer_ >index, < _function_ >callback) - _(void)_ - Retrieves a client by its index. `callback` has 2 parameters: < _Error_ >err, < _object_ >client.

* **getSink**(< _mixed_ >criteria, < _function_ >callback) - _(void)_ - Retrieves a sink by either its index (_integer_) or its name (_string_). `callback` has 2 parameters: < _Error_ >err, < _object_ >sink.

* **getSource**(< _mixed_ >criteria, < _function_ >callback) - _(void)_ - Retrieves a source by either its index (_integer_) or its name (_string_). `callback` has 2 parameters: < _Error_ >err, < _object_ >source.

* **getSinkInputByIndex**(< _integer_ >index, < _function_ >callback) - _(void)_ - Retrieves a sink input by its index. `callback` has 2 parameters: < _Error_ >err, < _object_ >sinkInput.

* **getSourceOutputByIndex**(< _integer_ >index, < _function_ >callback) - _(void)_ - Retrieves a source output by its index. `callback` has 2 parameters: < _Error_ >err, < _object_ >sourceOutput.

* **getCard**(< _mixed_ >criteria, < _function_ >callback) - _(void)_ - Retrieves a card by either its index (_integer_) or its name (_string_). `callback` has 2 parameters: < _Error_ >err, < _object_ >card.

* **getSinkIndexByName**(< _string_ >name, < _function_ >callback) - _(void)_ - Retrieves the index for a sink given its `name`. `callback` has 2 parameters: < _Error_ >err, < _integer_ >index.

* **getSourceIndexByName**(< _string_ >name, < _function_ >callback) - _(void)_ - Retrieves the index for a source given its `name`. `callback` has 2 parameters: < _Error_ >err, < _integer_ >index.

* **setSinkVolumes**(< _mixed_ >criteria, < _array_ >volumes, < _function_ >callback) - _(void)_ - Sets the volumes for each of a sink's channels. `criteria` can be an index (_integer_) or a name (_string_). `callback` has 1 parameter: < _Error_ >err.

* **setSourceVolumes**(< _mixed_ >criteria, < _array_ >volumes, < _function_ >callback) - _(void)_ - Sets the volumes for each of a source's channels. `criteria` can be an index (_integer_) or a name (_string_). `callback` has 1 parameter: < _Error_ >err.

* **setSinkInputVolumesByIndex**(< _integer_ >index, < _array_ >volumes, < _function_ >callback) - _(void)_ - Sets the volumes for each of a sink input's channels. `callback` has 1 parameter: < _Error_ >err.

* **setSourceOutputVolumesByIndex**(< _integer_ >index, < _array_ >volumes, < _function_ >callback) - _(void)_ - Sets the volumes for each of a source output's channels. `callback` has 1 parameter: < _Error_ >err.

* **setSinkMute**(< _mixed_ >criteria, < _boolean_ >muted, < _function_ >callback) - _(void)_ - Sets the muted status for a sink by either its index (_integer_) or its name (_string_). `callback` has 1 parameter: < _Error_ >err.

* **setSourceMute**(< _mixed_ >criteria, < _boolean_ >muted, < _function_ >callback) - _(void)_ - Sets the muted status for a source by either its index (_integer_) or its name (_string_). `callback` has 1 parameter: < _Error_ >err.

* **setSinkInputMuteByIndex**(< _integer_ >index, < _boolean_ >muted, < _function_ >callback) - _(void)_ - Sets the muted status for a sink input. `callback` has 1 parameter: < _Error_ >err.

* **setSourceOutputMuteByIndex**(< _integer_ >index, < _boolean_ >muted, < _function_ >callback) - _(void)_ - Sets the muted status for a source output. `callback` has 1 parameter: < _Error_ >err.

* **setSinkSuspend**(< _mixed_ >criteria, < _boolean_ >suspended, < _function_ >callback) - _(void)_ - Sets the suspended status for a sink by either its index (_integer_) or its name (_string_). `callback` has 1 parameter: < _Error_ >err.

* **setSourceSuspend**(< _mixed_ >criteria, < _boolean_ >suspended, < _function_ >callback) - _(void)_ - Sets the suspended status for a source by either its index (_integer_) or its name (_string_). `callback` has 1 parameter: < _Error_ >err.

* **setDefaultSinkByName**(< _string_ >name, < _function_ >callback) - _(void)_ - Sets the default sink. `callback` has 1 parameter: < _Error_ >err.

* **setDefaultSourceByName**(< _string_ >name, < _function_ >callback) - _(void)_ - Sets the default source. `callback` has 1 parameter: < _Error_ >err.

* **killClientByIndex**(< _integer_ >index, < _function_ >callback) - _(void)_ - Terminates the connection of the specified client. `callback` has 1 parameter: < _Error_ >err.

* **killSinkInputByIndex**(< _integer_ >index, < _function_ >callback) - _(void)_ - Terminates a sink input. `callback` has 1 parameter: < _Error_ >err.

* **killSourceOutputByIndex**(< _integer_ >index, < _function_ >callback) - _(void)_ - Terminates a source output. `callback` has 1 parameter: < _Error_ >err.

* **moveSinkInput**(< _integer_ >index, < _mixed_ >destSink, < _function_ >callback) - _(void)_ - Moves a sink input to a different sink identified by either its index (_integer_) or its name (_string_). `callback` has 1 parameter: < _Error_ >err.

* **moveSourceOutput**(< _integer_ >index, < _mixed_ >destSink, < _function_ >callback) - _(void)_ - Moves a source output to a different source identified by either its index (_integer_) or its name (_string_). `callback` has 1 parameter: < _Error_ >err.

* **setSinkPort**(< _mixed_ >criteria, < _string_ >portName, < _function_ >callback) - _(void)_ - Sets the port for a sink identified by either its index (_integer_) or its name (_string_). `callback` has 1 parameter: < _Error_ >err.

* **setSourcePort**(< _mixed_ >criteria, < _string_ >portName, < _function_ >callback) - _(void)_ - Sets the port for a source identified by either its index (_integer_) or its name (_string_). `callback` has 1 parameter: < _Error_ >err.

* **setCardProfile**(< _mixed_ >criteria, < _string_ >profileName, < _function_ >callback) - _(void)_ - Sets the profile for a card identified by either its index (_integer_) or its name (_string_). `callback` has 1 parameter: < _Error_ >err.

* **updateClientProperties**(< _object_ >properties, < _string_ >mode, < _function_ >callback) - _(void)_ - Updates this client's server-side properties. The update behavior is governed by `mode` which can be one of: `'set'` (any/all old properties are removed), `'update'` (only add properties that do not already exist), or `'replace'` (only overwrite property values for existing properties). `callback` has 1 parameter: < _Error_ >err.

* **removeClientProperties**(< _array_ >propertyNames, < _function_ >callback) - _(void)_ - Removes specified properties from this client's server-side properties. `callback` has 1 parameter: < _Error_ >err.

* **subscribe**(< _mixed_ >events, < _function_ >callback) - _(void)_ - Sets the event subscription for events emitted by the server. `events` can either be a _string_ or _array_ of strings containing one or more of: `'none'`, `'all'`, `'sink'`, `'source'`, `'sinkInput'`, `'sourceOutput'`, `'module'`, `'client'`, `'sampleCache'`, `'global'`, or `'card'`. `callback` has 1 parameter: < _Error_ >err.
