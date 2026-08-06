import allure
import pytest


pytestmark = [pytest.mark.snipeit, pytest.mark.api]


@allure.feature('Snipe-IT asset base data')
class TestAssetBaseData:

    @pytest.mark.smoke
    @allure.title('ASSET-001 Create the base data required by an asset')
    def test_create_asset_dependencies(
            self,
            snipeit_client,
            snipeit_resource_factory,
            unique_name,
    ):
        with allure.step('Verify the required built-in status labels'):
            response = snipeit_client.get('statuslabels', params={'limit': 100})
            assert response.status_code == 200
            status_by_name = {
                row['name']: row['type']
                for row in response.json()['rows']
            }
            assert status_by_name['Pending'] == 'pending'
            assert status_by_name['Ready to Deploy'] == 'deployable'
            assert status_by_name['Archived'] == 'archived'

        category_name = unique_name('category')
        manufacturer_name = unique_name('manufacturer')
        location_name = unique_name('location')
        model_name = unique_name('model')
        model_number = unique_name('model_number')

        with allure.step('Create an asset category'):
            category = snipeit_resource_factory.create('categories', {
                'name': category_name,
                'category_type': 'asset',
            })
            assert category['name'] == category_name

        with allure.step('Create a manufacturer'):
            manufacturer = snipeit_resource_factory.create('manufacturers', {
                'name': manufacturer_name,
            })
            assert manufacturer['name'] == manufacturer_name

        with allure.step('Create a location'):
            location = snipeit_resource_factory.create('locations', {
                'name': location_name,
            })
            assert location['name'] == location_name

        with allure.step('Create an asset model linked to its dependencies'):
            model = snipeit_resource_factory.create('models', {
                'name': model_name,
                'model_number': model_number,
                'category_id': category['id'],
                'manufacturer_id': manufacturer['id'],
            })
            assert model['name'] == model_name
            assert model['model_number'] == model_number
            assert model['category']['id'] == category['id']
            assert model['manufacturer']['id'] == manufacturer['id']
