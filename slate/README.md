# Run Slate for Local Development

To update the content and look of the Plato API Slate documentation, only change the files within the `slate/source` directory.

If you need to run Slate on your local machine to change and update the documentation, run the following command on the `slate` directory:

```shell
docker-compose up slate
```

Slate will be available on http://localhost:4567. If you need to update the served static content, just re-run the above command.

**Note**: This docker-compose file exists exclusively for the sake of local development. It should not be used to serve the documentation on the production environment.

To build the static content to the `slate/build` directory, change the "command" field on the slate docker-compose configuration to "build" (**Do not commit this change**) and run the following command:

```shell
docker-compose run --rm slate
```