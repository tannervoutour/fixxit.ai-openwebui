<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { getContext } from 'svelte';
	const i18n = getContext('i18n');

	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import { configureGroupDatabase, testDatabaseConnection, getGroupDatabaseConfig } from '$lib/apis/groups';

	export let groupId: string = null;
	export let edit = false;

	let connectionString = '';
	let password = '';
	let enabled = false;
	let loading = false;
	let testing = false;
	let testResult = null;

	const loadDatabaseConfig = async () => {
		if (!groupId || !edit) return;
		
		try {
			const config = await getGroupDatabaseConfig(localStorage.token, groupId);
			if (config && config.enabled !== undefined) {
				enabled = config.enabled;
				if (config.connection) {
					// Reconstruct connection string from config
					const conn = config.connection;
					if (conn.host && conn.port && conn.database && conn.user) {
						connectionString = `postgresql://${conn.user}@${conn.host}:${conn.port}/${conn.database}`;
					}
				}
			}
		} catch (error) {
			console.error('Error loading database config:', error);
		}
	};

	$: if (groupId && edit) {
		loadDatabaseConfig();
	}

	const testConnection = async () => {
		if (!connectionString || !password) {
			toast.error($i18n.t('Connection string and password are required'));
			return;
		}

		testing = true;
		testResult = null;

		try {
			const result = await testDatabaseConnection(localStorage.token, {
				connection_string: connectionString,
				password: password,
				enabled: enabled
			});

			testResult = result;
			if (result.success) {
				toast.success($i18n.t('Database connection successful'));
			} else {
				toast.error($i18n.t('Database connection failed: ') + result.message);
			}
		} catch (error) {
			console.error('Connection test error:', error);
			toast.error($i18n.t('Connection test failed'));
			testResult = { success: false, message: error.message || 'Unknown error' };
		} finally {
			testing = false;
		}
	};

	const saveConfiguration = async () => {
		if (!groupId) return false;

		if (enabled && (!connectionString || !password)) {
			toast.error($i18n.t('Connection string and password are required when database is enabled'));
			return false;
		}

		loading = true;

		try {
			await configureGroupDatabase(localStorage.token, groupId, {
				connection_string: connectionString,
				password: password,
				enabled: enabled
			});

			toast.success($i18n.t('Database configuration saved successfully'));
			return true;
		} catch (error) {
			console.error('Error saving database configuration:', error);
			toast.error($i18n.t('Error saving database configuration: ') + (error.message || 'Unknown error'));
			return false;
		} finally {
			loading = false;
		}
	};

	// Export the save function for parent component
	export { saveConfiguration as save };
</script>

<div class="flex flex-col space-y-4">
	<div class="text-sm text-gray-600 dark:text-gray-400">
		{$i18n.t('Configure external database connection for logs storage.')}
	</div>

	<!-- Enable/Disable Toggle -->
	<div class="flex items-center space-x-3">
		<input
			type="checkbox"
			id="database-enabled"
			bind:checked={enabled}
			class="rounded border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-blue-600 focus:ring-blue-500"
		/>
		<label for="database-enabled" class="text-sm font-medium text-gray-900 dark:text-gray-100">
			{$i18n.t('Enable database integration')}
		</label>
	</div>

	{#if enabled}
		<div class="space-y-4 pl-6 border-l-2 border-gray-200 dark:border-gray-700">
			<!-- Connection String Input -->
			<div>
				<label for="connection-string" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
					{$i18n.t('PostgreSQL Connection String')}
				</label>
				<input
					id="connection-string"
					bind:value={connectionString}
					type="text"
					placeholder="postgresql://user@host:port/database"
					class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm focus:border-blue-500 focus:ring-blue-500"
					required={enabled}
				/>
				<div class="mt-1 text-xs text-gray-500 dark:text-gray-400">
					{$i18n.t('Format: postgresql://username@hostname:port/database_name')}
				</div>
			</div>

			<!-- Password Input -->
			<div>
				<label for="database-password" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
					{$i18n.t('Database Password')}
				</label>
				<SensitiveInput
					id="database-password"
					bind:value={password}
					placeholder={edit ? $i18n.t('Enter new password or leave blank to keep current') : $i18n.t('Enter database password')}
					required={enabled && !edit}
				/>
			</div>

			<!-- Test Connection Button -->
			<div class="flex items-center space-x-3">
				<button
					type="button"
					on:click={testConnection}
					disabled={testing || !connectionString || !password}
					class="px-4 py-2 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
				>
					{#if testing}
						<Spinner className="size-4" />
						<span>{$i18n.t('Testing...')}</span>
					{:else}
						<svg class="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
						<span>{$i18n.t('Test Connection')}</span>
					{/if}
				</button>

				{#if testResult}
					<div class="flex items-center space-x-1">
						{#if testResult.success}
							<svg class="size-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
							</svg>
							<span class="text-sm text-green-600 dark:text-green-400">{$i18n.t('Connection successful')}</span>
						{:else}
							<svg class="size-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
							<span class="text-sm text-red-600 dark:text-red-400">{$i18n.t('Connection failed')}</span>
						{/if}
					</div>
				{/if}
			</div>

			<!-- Connection Status Info -->
			{#if testResult && !testResult.success && testResult.message}
				<div class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
					<div class="text-sm text-red-800 dark:text-red-200">
						<strong>{$i18n.t('Error:')}</strong> {testResult.message}
					</div>
				</div>
			{/if}

			<!-- Help Text -->
			<div class="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
				<div class="text-sm text-blue-800 dark:text-blue-200">
					<div class="font-medium mb-2">{$i18n.t('Database Setup Instructions:')}</div>
					<ul class="space-y-1 text-xs list-disc list-inside">
						<li>{$i18n.t('Ensure your Supabase database is accessible from this server')}</li>
						<li>{$i18n.t('The database should contain the required logs and equipment_groups tables')}</li>
						<li>{$i18n.t('Connection will be encrypted and stored securely')}</li>
						<li>{$i18n.t('Test the connection before saving to ensure it works properly')}</li>
					</ul>
				</div>
			</div>
		</div>
	{/if}
</div>